#!/usr/bin/env python3

from pathlib import Path
import sys

IMPL = (
    Path(__file__).resolve().parent
    / "comparator_benchmark_execution_v1_impl"
)

sys.path.insert(0, str(IMPL))

import adapters


def require(condition, message):
    if not condition:
        raise AssertionError(message)


table = (
    "node\tsite_1\tsite_2\n"
    "root\tA\tC\n"
    "root\t\tT\n"
    "n0\tA\tC\n"
    "n0\tG\t\n"
    "n00\tA\tT\n"
    "A\tA\tC\n"
    "B\tG\tC\n"
    "C\tA\tT\n"
    "D\tA\tT\n"
)

observed = adapters.parse_tabular_node_states(
    table,
    [1, 2],
)

expected = {
    "root": "AN",
    "n0": "NC",
    "n00": "AT",
    "A": "AC",
    "B": "GC",
    "C": "AT",
    "D": "AT",
}

require(
    observed == expected,
    f"PastML ambiguity parsing differs: {observed!r}",
)

print("PASS | singleton states retained")
print("PASS | repeated multi-state calls encoded as N")


tree = "(A:0.1,B:0.1)root;"

ambiguous_sequences = {
    "root": "NC",
    "A": "AC",
    "B": "GC",
}

events = adapters.events_from_node_sequences(
    tree,
    ambiguous_sequences,
    method="PastML",
    scenario_id="toy_ambiguity",
)

require(
    events == [],
    f"ambiguous branch endpoint unexpectedly emitted events: {events!r}",
)

print("PASS | N endpoint does not emit a discrete branch event")


resolved_sequences = {
    "root": "AC",
    "A": "GC",
    "B": "AC",
}

events = adapters.events_from_node_sequences(
    tree,
    resolved_sequences,
    method="PastML",
    scenario_id="toy_resolved",
)

require(
    len(events) == 1,
    f"expected one resolved event; observed {events!r}",
)

event = events[0]

require(event["position"] == "1", "resolved event position differs")
require(event["ancestral_state"] == "A", "resolved ancestral state differs")
require(event["derived_state"] == "G", "resolved derived state differs")

print("PASS | resolved A-to-G event remains detectable")
print("PASTML_AMBIGUITY_AMENDMENT_TEST=PASS")

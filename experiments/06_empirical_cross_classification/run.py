from __future__ import annotations
import re, hashlib, json, csv, sys, argparse, os, platform, time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Tuple, Set
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import numba
from numba import njit

STATES='ACGT'
STATE_TO_INT={c:i for i,c in enumerate(STATES)}
INF=30000

class Node:
    __slots__=('name','children','id')
    def __init__(self,name=''):
        self.name=name; self.children=[]; self.id=-1

class NewickParser:
    def __init__(self,text):
        self.s=re.sub(r'\[[^\]]*\]','',text.strip()); self.i=0; self.n=len(self.s)
    def skip(self):
        while self.i<self.n and self.s[self.i].isspace(): self.i+=1
    def label(self):
        self.skip()
        if self.i>=self.n: return ''
        if self.s[self.i]=="'":
            self.i+=1; out=[]
            while self.i<self.n:
                if self.s[self.i]=="'":
                    if self.i+1<self.n and self.s[self.i+1]=="'": out.append("'"); self.i+=2; continue
                    self.i+=1; break
                out.append(self.s[self.i]); self.i+=1
            return ''.join(out)
        start=self.i
        while self.i<self.n and self.s[self.i] not in ',():;': self.i+=1
        return self.s[start:self.i].strip()
    def branch_length(self):
        self.skip()
        if self.i<self.n and self.s[self.i]==':':
            self.i+=1
            while self.i<self.n and self.s[self.i] not in ',();': self.i+=1
    def subtree(self):
        self.skip()
        if self.s[self.i]=='(':
            self.i+=1; ch=[]
            while True:
                ch.append(self.subtree()); self.skip()
                if self.s[self.i]==',': self.i+=1; continue
                if self.s[self.i]==')': self.i+=1; break
                raise ValueError(f'bad newick near {self.s[self.i:self.i+30]}')
            name=self.label(); self.branch_length(); nd=Node(name); nd.children=ch; return nd
        name=self.label(); self.branch_length(); return Node(name)
    def parse(self):
        root=self.subtree(); self.skip()
        if self.i<self.n and self.s[self.i]==';': self.i+=1
        self.skip()
        if self.i!=self.n: raise ValueError('trailing newick content')
        return root

def parse_nexus(path: Path, renames=None):
    renames=renames or {}
    text=path.read_text()
    m=re.search(r'(?is)\btaxlabels\b(.*?);',text)
    if not m: raise ValueError(f'No TAXLABELS in {path}')
    raw=m.group(1)
    # labels in these canonical inputs are unquoted, but support NEXUS single quotes.
    labels=[]; i=0
    while i<len(raw):
        while i<len(raw) and raw[i].isspace(): i+=1
        if i>=len(raw): break
        if raw[i]=="'":
            i+=1; out=[]
            while i<len(raw):
                if raw[i]=="'":
                    if i+1<len(raw) and raw[i+1]=="'": out.append("'"); i+=2; continue
                    i+=1; break
                out.append(raw[i]); i+=1
            labels.append(''.join(out))
        else:
            j=i
            while j<len(raw) and not raw[j].isspace(): j+=1
            labels.append(raw[i:j]); i=j
    labels=[renames.get(x,x) for x in labels]
    mm=re.search(r'(?is)\bmatrix\b(.*?);',text)
    if not mm: raise ValueError(f'No MATRIX in {path}')
    site_ids=[]; rows=[]
    for line in mm.group(1).splitlines():
        s=line.strip()
        if not s: continue
        parts=s.split()
        site=parts[0]; toks=parts[1:]
        if len(toks)==1 and len(toks[0])==len(labels): seq=list(toks[0])
        else: seq=toks
        if len(seq)!=len(labels): raise ValueError((path,site,len(seq),len(labels)))
        try: arr=[STATE_TO_INT[x.upper()] for x in seq]
        except KeyError as e: raise ValueError(f'Unsupported state {e} in {path}')
        site_ids.append(site); rows.append(arr)
    return labels, site_ids, np.asarray(rows,dtype=np.uint8)

def flatten_tree(root: Node):
    nodes=[]
    def walk(n):
        n.id=len(nodes); nodes.append(n)
        for c in n.children: walk(c)
    walk(root)
    adj=[set() for _ in nodes]
    for n in nodes:
        for c in n.children:
            adj[n.id].add(c.id); adj[c.id].add(n.id)
    return nodes,adj,root.id

def tips_on_side(adj,nodes,u,v):
    st=[u]; seen={v}; tips=[]
    while st:
        x=st.pop()
        if x in seen: continue
        seen.add(x)
        if len(adj[x])==1 and nodes[x].name: tips.append(nodes[x].name)
        for y in adj[x]:
            if y not in seen: st.append(y)
    return set(tips)

def orient_tree(tree_path: Path, rooting: str, outgroup=()):
    parsed=NewickParser(tree_path.read_text()).parse()
    nodes,adj,parsed_root=flatten_tree(parsed)
    if rooting=='outgroup':
        # suppress degree-two encoded root before rerooting
        if len(adj[parsed_root])==2:
            a,b=tuple(adj[parsed_root]); adj[a].remove(parsed_root); adj[b].remove(parsed_root); adj[a].add(b); adj[b].add(a); adj[parsed_root].clear()
        target=set(outgroup); found=None
        for u in range(len(nodes)):
            for v in list(adj[u]):
                if u<v:
                    side=tips_on_side(adj,nodes,u,v)
                    if side==target or (set(n.name for n in nodes if n.name and len(adj[n.id])==1)-side)==target:
                        if side==target: found=(u,v)
                        else: found=(v,u)
                        break
            if found: break
        if not found: raise ValueError(f'outgroup edge not found {target}')
        u,v=found
        adj[u].remove(v); adj[v].remove(u)
        root=len(nodes); nodes.append(Node('')); nodes[-1].id=root; adj.append({u,v}); adj[u].add(root); adj[v].add(root)
    elif rooting=='existing': root=parsed_root
    else: raise ValueError(rooting)
    n=len(nodes); parent=np.full(n,-1,dtype=np.int32); order=[]; stack=[root]; parent[root]=root
    while stack:
        x=stack.pop(); order.append(x)
        for y in adj[x]:
            if parent[y]!=-1: continue
            parent[y]=x; stack.append(y)
    if any(parent<0):
        # suppressed parsed root is disconnected; ignore it by compacting reachable nodes
        reachable=order
        remap={old:i for i,old in enumerate(reachable)}
        newnodes=[nodes[old] for old in reachable]
        newadj=[set() for _ in newnodes]
        for old in reachable:
            for y in adj[old]:
                if y in remap: newadj[remap[old]].add(remap[y])
        nodes,adj=newnodes,newadj; root=remap[root]; n=len(nodes)
        parent=np.full(n,-1,dtype=np.int32); order=[]; stack=[root]; parent[root]=root
        while stack:
            x=stack.pop(); order.append(x)
            for y in adj[x]:
                if parent[y]!=-1: continue
                parent[y]=x; stack.append(y)
    children=[[] for _ in range(n)]
    for x in range(n):
        if x!=root: children[parent[x]].append(x)
    # stable child ordering not analytically relevant
    offs=np.zeros(n+1,dtype=np.int32); flat=[]
    for i,ch in enumerate(children): offs[i+1]=offs[i]+len(ch); flat.extend(ch)
    flat=np.asarray(flat,dtype=np.int32)
    preorder=np.asarray(order,dtype=np.int32)
    postorder=np.asarray(order[::-1],dtype=np.int32)
    tips=[i for i in range(n) if len(children[i])==0]
    names=[nodes[i].name for i in tips]
    if any(not x for x in names): raise ValueError('unnamed tip')
    if len(names)!=len(set(names)): raise ValueError('duplicate tips')
    # descendant tip lists/counts
    desc=[None]*n
    for x in postorder:
        x=int(x)
        if len(children[x])==0: desc[x]=(nodes[x].name,)
        else:
            vals=[]
            for c in children[x]: vals.extend(desc[c])
            desc[x]=tuple(sorted(vals))
    desc_count=np.asarray([len(desc[i]) for i in range(n)],dtype=np.int32)
    branch_id=['']*n
    for i in range(n):
        if i==root: continue
        payload=''.join(x+'\n' for x in desc[i]).encode()
        branch_id[i]='b_'+hashlib.sha256(payload).hexdigest()
    return dict(nodes=nodes,parent=parent,children=children,offs=offs,flat=flat,preorder=preorder,postorder=postorder,root=root,tips=tips,names=names,desc=desc,desc_count=desc_count,branch_id=branch_id)

@njit(cache=True)
def analyze(states, tip_nodes, offs, flat, preorder, postorder, parent, root, desc_count):
    nsites=states.shape[0]; nnodes=parent.shape[0]; nedges=nnodes-1
    edge_nodes=np.empty(nedges,dtype=np.int32); k=0
    for x in range(nnodes):
        if x!=root: edge_nodes[k]=x; k+=1
    status=np.zeros((nsites,nedges),dtype=np.uint8)
    fixed=np.zeros((nsites,nedges),dtype=np.uint8)
    masks=np.zeros((nsites,nedges),dtype=np.uint16)
    scores=np.zeros(nsites,dtype=np.int16)
    D=np.empty((nnodes,4),dtype=np.int16); O=np.empty((nnodes,4),dtype=np.int16); cnt=np.empty((nnodes,4),dtype=np.int16)
    for si in range(nsites):
        for x in range(nnodes):
            for a in range(4): D[x,a]=INF; O[x,a]=INF; cnt[x,a]=0
        for ti in range(tip_nodes.shape[0]):
            x=tip_nodes[ti]; s=states[si,ti]
            for a in range(4): D[x,a]=0 if a==s else INF
            cnt[x,s]=1
        for ii in range(postorder.shape[0]):
            x=postorder[ii]
            if offs[x+1]==offs[x]: continue
            for a in range(4):
                total=0
                for jj in range(offs[x],offs[x+1]):
                    c=flat[jj]; best=INF
                    for b in range(4):
                        val=D[c,b]+(0 if a==b else 1)
                        if val<best: best=val
                    total+=best
                D[x,a]=total
            for jj in range(offs[x],offs[x+1]):
                c=flat[jj]
                for a in range(4): cnt[x,a]+=cnt[c,a]
        best=D[root,0]
        for a in range(1,4):
            if D[root,a]<best: best=D[root,a]
        scores[si]=best
        for a in range(4): O[root,a]=0
        for ii in range(preorder.shape[0]):
            p=preorder[ii]
            for jj in range(offs[p],offs[p+1]):
                c=flat[jj]
                for b in range(4):
                    ob=INF
                    for a in range(4):
                        cbest=INF
                        for y in range(4):
                            val=D[c,y]+(0 if a==y else 1)
                            if val<cbest: cbest=val
                        val=O[p,a]+(D[p,a]-cbest)+(0 if a==b else 1)
                        if val<ob: ob=val
                    O[c,b]=ob
        totalcnt=np.empty(4,dtype=np.int16)
        for a in range(4): totalcnt[a]=cnt[root,a]
        for ei in range(nedges):
            c=edge_nodes[ei]; p=parent[c]; mask=0; npairs=0; same=False; change=False
            for a in range(4):
                cbest=INF
                for y in range(4):
                    val=D[c,y]+(0 if a==y else 1)
                    if val<cbest: cbest=val
                base=O[p,a]+(D[p,a]-cbest)
                for b in range(4):
                    val=base+(0 if a==b else 1)+D[c,b]
                    if val==best:
                        mask |= 1 << (a*4+b); npairs+=1
                        if a==b: same=True
                        else: change=True
            masks[si,ei]=mask
            if not change: st=0
            elif npairs==1: st=1
            elif not same: st=2
            else: st=3
            status[si,ei]=st
            dn=desc_count[c]
            fx=0
            for a in range(4):
                if cnt[c,a]==dn and totalcnt[a]==dn:
                    fx=1; break
            fixed[si,ei]=fx
    return edge_nodes,status,fixed,masks,scores

def mask_pairs(mask):
    out=[]
    for a in range(4):
        for b in range(4):
            if mask & (1<<(a*4+b)): out.append(f'{STATES[a]}>{STATES[b]}')
    return '|'.join(out)

def unique_pair(mask):
    vals=[]
    for a in range(4):
        for b in range(4):
            if mask & (1<<(a*4+b)): vals.append((a,b))
    return vals[0] if len(vals)==1 else None

@dataclass
class DS:
    id:str
    name:str
    aln:Path
    tree:Path
    rooting:str
    outgroup:Tuple[str,...]=()
    renames:dict|None=None

INPUT_HASHES = {
    "ak3_alignment.nex": "40c49b026c52e04530ecbbee7044567ac3355eccf7adda42a7d96bf977df9014",
    "ak3_tree.nwk": "18322b2808baf621d09dd5292027205e68a0f207d7be44f043bd044d0d314bd0",
    "st97_alignment.nex": "3e7a631c2780e1aeb7f6d3b600f2d7a08742b2351eb22edbd10a3ca0b3ca591c",
    "st97_tree.nwk": "7f71657597b9dd62db8c93570c0afd251e5677c3657b1654e71b58a2a15949ad",
    "oxa48_alignment.nex": "60940e7fca31849396ed070f79299055a762f4b5192dd18918fb84f300deda9b",
    "oxa48_tree.nwk": "fb1895907fbbff4cb2e74d7ad564c12e9b80d07f5800b6007618dcb3b82f2540",
    "clade_a_alignment.nex": "fd7dc8c8404766a6ab0354cb245c8e0befc016a0c480c79bb3395a40f49e7f30",
    "clade_a_tree.nwk": "807b23612aa5dfad37080c66386579e3c3dcc04855639f95909b87f134065d55",
    "clade_b_alignment.nex": "6fff544b576725253c2c5b0720e7491592ca1c26c10bc78a9ce6a4481ab3c7b7",
    "clade_b_tree.nwk": "b5c1ba809e787e5eebf8d27aae99e8cb49c0f0edac1a0bc5a85d331644dff67b",
}

EXPECTED_DATASET = {
    "ak3": (396,10481,788,8259028,10584,10249,287,48),
    "st97": (103,4651,202,939502,4604,4552,52,0),
    "oxa48": (47,266,90,23940,257,252,1,4),
    "clade_a": (120,3911,236,922996,4003,3750,178,75),
    "clade_b": (246,12148,488,5928224,12196,12014,157,25),
}
EXPECTED_TOTAL = (912,31457,1804,16073690,31644,30817,675,152)
EXPECTED_MECHANISMS = {"derived_state_outside":645,"descendant_not_fixed":30}
EXPECTED_ROOT = {
    "ak3": (2,244,242,2), "st97": (2,160,160,0), "oxa48": (2,26,26,0),
    "clade_a": (2,172,141,31), "clade_b": (2,138,134,4),
}

def sha256_file(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()

def make_datasets(inp:Path):
    return [
        DS('ak3','MRSA AK3',inp/'ak3_alignment.nex',inp/'ak3_tree.nwk','outgroup',('SRR13968194',),{}),
        DS('st97','MRSA ST97',inp/'st97_alignment.nex',inp/'st97_tree.nwk','outgroup',('ERR4911723',),{}),
        DS('oxa48','E. coli ST131/OXA-48',inp/'oxa48_alignment.nex',inp/'oxa48_tree.nwk','outgroup',('ERR1852604','ERR1791001','ERR1791000','ERR1791004'),{'REF':'18AR0845'}),
        DS('clade_a','E. coli ST131 Clade A',inp/'clade_a_alignment.nex',inp/'clade_a_tree.nwk','existing',(),{}),
        DS('clade_b','E. coli ST131 Clade B',inp/'clade_b_alignment.nex',inp/'clade_b_tree.nwk','existing',(),{}),
    ]

def parse_position(site_id:str)->str:
    m=re.search(r'_(\d+)$',site_id)
    return m.group(1) if m else ''

def write_tsv(path:Path, header, rows):
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.writer(f,delimiter='\t',lineterminator='\n'); w.writerow(header); w.writerows(rows)


def production_source_metadata(branchsnv_root:Path):
    source=branchsnv_root/'src'/'branchsnv'
    init=(source/'__init__.py').read_text(encoding='utf-8')
    m=re.search(r'__version__\s*=\s*[\"\']([^\"\']+)',init)
    if not m: raise ValueError('Unable to read BRANCHSNV version from production source')
    return {
        'branchsnv_version':m.group(1),
        'branchsnv_analysis_sha256':sha256_file(source/'analysis.py'),
        'branchsnv_parsimony_sha256':sha256_file(source/'parsimony.py'),
    }

def parse_args():
    p=argparse.ArgumentParser(description='Exhaustive five-phylogeny cross-classification of fixed exclusivity and focal-edge parsimony.')
    p.add_argument('--branchsnv-root',required=True,type=Path)
    p.add_argument('--input-dir',required=True,type=Path)
    p.add_argument('--output-dir',required=True,type=Path)
    return p.parse_args()

def main():
    args=parse_args(); inp=args.input_dir.resolve(); out=args.output_dir.resolve(); root=args.branchsnv_root.resolve(); out.mkdir(parents=True,exist_ok=True)
    prodmeta=production_source_metadata(root)
    started=datetime.now(timezone.utc).isoformat(); start=time.perf_counter()
    input_checks=[]
    for name,expected in INPUT_HASHES.items():
        observed=sha256_file(inp/name); input_checks.append((name,expected,observed,int(expected==observed)))
        if observed!=expected: raise ValueError(f'Input checksum mismatch for {name}: {observed}')
    write_tsv(out/'input_checksums.tsv',['file','expected_sha256','observed_sha256','match'],input_checks)
    dsrows=[]; branchrows=[]; eventrows=[]; rootrows=[]
    for ds in make_datasets(inp):
        labels,site_ids,states=parse_nexus(ds.aln,ds.renames or {})
        tr=orient_tree(ds.tree,ds.rooting,ds.outgroup)
        if set(labels)!=set(tr['names']): raise ValueError(f'{ds.id}: alignment/tree taxon mismatch after documented normalization')
        name_to_node={tr['nodes'][i].name:i for i in tr['tips']}; tip_nodes=np.asarray([name_to_node[x] for x in labels],dtype=np.int32)
        edge_nodes,status,fixed,masks,scores=analyze(states,tip_nodes,tr['offs'],tr['flat'],tr['preorder'],tr['postorder'],tr['parent'],tr['root'],tr['desc_count'])
        edge_index={int(c):i for i,c in enumerate(edge_nodes)}
        nsites=len(site_ids); elig=comps=inf=both=unf=place=stateamb=fixed_nonun=0
        label_index={name:i for i,name in enumerate(labels)}
        for c0 in edge_nodes:
            c=int(c0); ei=edge_index[c]; rootadj=tr['parent'][c]==tr['root']; terminal=(tr['offs'][c+1]==tr['offs'][c])
            st=status[:,ei]; fx=fixed[:,ei].astype(bool); info=fx | (st>0)
            ninf=int(info.sum()); nboth=int((fx & (st==1)).sum()); nunf=int((~fx & (st==1)).sum()); npl=int((st==3).sum()); nsa=int((st==2).sum()); nfn=int((fx & (st!=1)).sum())
            branchrows.append((ds.id,tr['branch_id'][c],int(tr['desc_count'][c]),'terminal' if terminal else 'internal',int(rootadj),nsites,ninf,nboth,nunf,npl,nsa,nfn))
            if rootadj:
                rootrows.append((ds.id,tr['branch_id'][c],int(tr['desc_count'][c]),ninf,int((fx & (st==3)).sum()),int((~fx & (st==3)).sum())))
            else:
                elig+=1; comps+=nsites; inf+=ninf; both+=nboth; unf+=nunf; place+=npl; stateamb+=nsa; fixed_nonun+=nfn
            desc_cols=np.asarray([label_index[n] for n in tr['desc'][c]],dtype=np.int32)
            for si0 in np.nonzero(info)[0]:
                si=int(si0); mask=int(masks[si,ei]); stv=int(st[si]); fxv=bool(fx[si]); pair=unique_pair(mask); mech=''; change=''
                if pair is not None and pair[0]!=pair[1]: change=f'{STATES[pair[0]]}>{STATES[pair[1]]}'
                if stv==1 and not fxv and pair is not None:
                    der=pair[1]; vals=states[si,desc_cols]; outside_n=int(np.sum(states[si,:]==der))-int(np.sum(vals==der))
                    mech='derived_state_outside' if np.all(vals==der) and outside_n>0 else 'descendant_not_fixed'
                eventrows.append((ds.id,tr['branch_id'][c],int(tr['desc_count'][c]),'terminal' if terminal else 'internal',int(rootadj),site_ids[si],parse_position(site_ids[si]),int(scores[si]),mask_pairs(mask),['no_change','unambiguous_change','change_state_ambiguous','placement_ambiguous'][stv],str(int(fxv)),change,mech))
        dsrows.append((ds.id,ds.name,len(labels),nsites,elig,comps,inf,both,unf,place,stateamb,fixed_nonun))
    write_tsv(out/'dataset_summary.tsv',['dataset','dataset_name','taxa','variable_sites','eligible_non_root_adjacent_branches','branch_site_comparisons','informative','both','unambiguous_not_fixed','placement_ambiguous','change_state_ambiguous','fixed_without_unambiguous'],dsrows)
    write_tsv(out/'branch_cross_classification.tsv',['dataset','branch_id','descendant_count','branch_type','root_adjacent','sites','informative','both','unambiguous_not_fixed','placement_ambiguous','change_state_ambiguous','fixed_without_unambiguous'],branchrows)
    write_tsv(out/'informative_events.tsv',['dataset','branch_id','descendant_count','branch_type','root_adjacent','site_id','position','parsimony_score','possible_pairs','parsimony_status','fixed_exclusive','change','nonexclusivity_mechanism'],eventrows)
    write_tsv(out/'root_adjacent.tsv',['dataset','branch_id','descendant_count','informative','fixed_plus_placement','not_fixed_plus_placement'],rootrows)
    # Use pandas for compact stratification and as an independent table-level aggregation layer.
    bdf=pd.DataFrame(branchrows,columns=['dataset','branch_id','descendant_count','branch_type','root_adjacent','sites','informative','both','unambiguous_not_fixed','placement_ambiguous','change_state_ambiguous','fixed_without_unambiguous'])
    primary=bdf[bdf.root_adjacent==0]
    strata=[]
    for typ,g in primary.groupby('branch_type',sort=True):
        strata.append((typ,len(g),int(g.sites.sum()),int(g.informative.sum()),int(g.both.sum()),int(g.unambiguous_not_fixed.sum()),int(g.placement_ambiguous.sum())))
    write_tsv(out/'branch_stratification.tsv',['branch_type','branches','branch_site_comparisons','informative','both','unambiguous_not_fixed','placement_ambiguous'],strata)
    mech={k:0 for k in EXPECTED_MECHANISMS}
    for r in eventrows:
        if r[-1]: mech[r[-1]]=mech.get(r[-1],0)+1
    write_tsv(out/'mechanism_summary.tsv',['mechanism','events'],sorted(mech.items()))
    observed_dataset={r[0]:(r[2],r[3],r[4],r[5],r[6],r[7],r[8],r[9]) for r in dsrows}
    dataset_expected_pass=all(observed_dataset[k]==v for k,v in EXPECTED_DATASET.items())
    total=(sum(r[2] for r in dsrows),sum(r[3] for r in dsrows),sum(r[4] for r in dsrows),sum(r[5] for r in dsrows),sum(r[6] for r in dsrows),sum(r[7] for r in dsrows),sum(r[8] for r in dsrows),sum(r[9] for r in dsrows))
    root_obs={k:(sum(1 for r in rootrows if r[0]==k),sum(r[3] for r in rootrows if r[0]==k),sum(r[4] for r in rootrows if r[0]==k),sum(r[5] for r in rootrows if r[0]==k)) for k in EXPECTED_ROOT}
    root_pass=root_obs==EXPECTED_ROOT
    summary={'schema_version':1,'experiment':'06_empirical_cross_classification_analysis','datasets':len(dsrows),'totals':{'taxa':total[0],'variable_sites':total[1],'eligible_non_root_adjacent_branches':total[2],'branch_site_comparisons':total[3],'informative':total[4],'both':total[5],'unambiguous_not_fixed':total[6],'placement_ambiguous':total[7],'outside_intersection':total[6]+total[7]},'nonexclusivity_mechanisms':mech,'root_adjacent_sensitivity':{'informative':sum(r[3] for r in rootrows),'fixed_plus_placement':sum(r[4] for r in rootrows),'not_fixed_plus_placement':sum(r[5] for r in rootrows)},'three_dataset_snapshot':{'branch_rows':sum(1 for r in branchrows if r[0] in {'ak3','st97','oxa48'}),'informative_records_including_root_adjacent':sum(1 for r in eventrows if r[0] in {'ak3','st97','oxa48'})},'expected_dataset_totals_match':dataset_expected_pass,'expected_global_totals_match':total==EXPECTED_TOTAL,'expected_mechanisms_match':mech==EXPECTED_MECHANISMS,'expected_root_sensitivity_match':root_pass,'software':{'numpy':np.__version__,'pandas':pd.__version__,'numba':numba.__version__},'production_source':prodmeta,'input_transformations':[{'dataset':'oxa48','operation':'analysis-only taxon-label normalization REF→18AR0845 before tree/alignment matching'}]}
    summary['overall_pass']=all([summary['expected_dataset_totals_match'],summary['expected_global_totals_match'],summary['expected_mechanisms_match'],summary['expected_root_sensitivity_match'],summary['three_dataset_snapshot']['branch_rows']==1086,summary['three_dataset_snapshot']['informative_records_including_root_adjacent']==15875])
    (out/'analysis_summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n',encoding='utf-8',newline='\n')
    meta={'experiment':'06_empirical_cross_classification_analysis','started_utc':started,'completed_utc':datetime.now(timezone.utc).isoformat(),'elapsed_seconds':round(time.perf_counter()-start,6),'python_version':platform.python_version(),'platform':platform.platform(),'machine':platform.machine(),'processor':platform.processor(),'cpu_count':os.cpu_count(),**prodmeta,'validation_script_sha256':sha256_file(Path(__file__).resolve()),'exit_status':'PASS' if summary['overall_pass'] else 'FAIL'}
    (out/'analysis_run_metadata.json').write_text(json.dumps(meta,indent=2,sort_keys=True)+'\n',encoding='utf-8',newline='\n')
    print(f"Informative comparisons: {total[4]:,}; both={total[5]:,}; unambiguous-not-fixed={total[6]:,}; placement-ambiguous={total[7]:,}")
    print('ANALYSIS PASS' if summary['overall_pass'] else 'ANALYSIS FAIL')
    return 0 if summary['overall_pass'] else 1

if __name__=='__main__': raise SystemExit(main())

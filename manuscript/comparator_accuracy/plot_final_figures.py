#!/usr/bin/env python3
"""Reproduce assembled BRANCHSNV Experiment 07 main and supplementary figures.

Inputs are frozen accuracy tables and published analysis intervals. The input
archive is verified against its exact SHA256; every component listed in its
SHA256SUMS is checked before any plotting. All plotted numeric points derive
from these tables. Panel a of the main figure is an explicitly illustrative
four-tip site with one unresolved character, drawn from code (not a scenario).
"""
from __future__ import annotations
import hashlib, io, json, math, os, subprocess, tarfile
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.gridspec import GridSpec, GridSpecFromSubplotSpec
from matplotlib.lines import Line2D
from matplotlib.patches import Circle

HERE = Path(__file__).resolve().parent
ARCHIVE = HERE/'BRANCHSNV_Experiment07_FINAL_RESULTS.tar.gz'
EXPECTED_ARCHIVE_SHA = 'cf9ef552a8849343a288f65a8dc07c2e6a359ec2e8b538f08ab6febe129075af'
OUT = HERE/'figures'
OUT.mkdir(exist_ok=True)
METHODS = ['ARPIP','FastML','PAML','TreeTime','BRANCHSNV','SNPPar','PastML']
REC_METHODS = ['TreeTime','SNPPar','HomoplasyFinder','POUTINE']
REGIMES = ['unique_only','parallel','convergent','reversal','mixed_recurrence']
REGIMES_SHORT = {'unique_only':'Unique','parallel':'Parallel','convergent':'Convergent','reversal':'Reversal','mixed_recurrence':'Mixed'}
MARK = {'BRANCHSNV':'D','ARPIP':'o','FastML':'s','PAML':'^','TreeTime':'v','SNPPar':'X','PastML':'P','HomoplasyFinder':'h','POUTINE':'*'}
GRAY = {'BRANCHSNV':'#111111','ARPIP':'#545454','FastML':'#777777','PAML':'#555555','TreeTime':'#9a9a9a','SNPPar':'#727272','PastML':'#b2b2b2','HomoplasyFinder':'#888888','POUTINE':'#bbbbbb'}

plt.rcParams.update({
    'font.family':'DejaVu Sans','font.size':7.0,'axes.titlesize':8.3,
    'axes.titleweight':'semibold','axes.labelsize':7.2,'xtick.labelsize':6.5,
    'ytick.labelsize':6.5,'axes.linewidth':0.65,'xtick.major.width':0.6,
    'ytick.major.width':0.6,'xtick.major.size':3,'ytick.major.size':3,
    'pdf.fonttype':42, 'ps.fonttype':42, 'svg.fonttype':'none',
    'svg.hashsalt':'BRANCHSNV-Experiment07-figure-set-v4',
    'savefig.facecolor':'white'
})


def verify_inputs():
    actual = hashlib.sha256(ARCHIVE.read_bytes()).hexdigest()
    if actual != EXPECTED_ARCHIVE_SHA:
        raise RuntimeError(f'Wrong source archive SHA256: {actual}')
    unpack = HERE/'_source'
    unpack.mkdir(exist_ok=True)
    with tarfile.open(ARCHIVE) as tar:
        for m in tar.getmembers():
            if m.issym() or m.islnk() or m.name.startswith('/') or '..' in Path(m.name).parts:
                raise RuntimeError(f'Unsafe archive member: {m.name}')
        tar.extractall(unpack, filter='data')
    d = unpack/'independent_scoring_extension_v1'
    subprocess.run(['sha256sum','-c','SHA256SUMS'],cwd=d,check=True,stdout=subprocess.DEVNULL)
    return d


def read():
    src = verify_inputs()
    branch = pd.read_csv(src/'combined_branch_event_accuracy.tsv',sep='\t').set_index('method').loc[METHODS]
    recurrence = pd.read_csv(src/'combined_recurrent_site_accuracy.tsv',sep='\t').set_index('method').loc[REC_METHODS]
    frozen = pd.read_csv(src/'frozen_primary_3_method_comparative_aggregate_scores.tsv',sep='\t')
    per = pd.read_csv(src/'per_scenario_scores.tsv',sep='\t')
    agg = pd.read_csv(src/'aggregate_scores.tsv',sep='\t')
    boot = pd.read_csv(HERE/'paired_stratum_bootstrap_differences.csv')
    rec_boot = pd.read_csv(HERE/'recurrent_scenario_bootstrap_differences.csv')
    # Enforce exact original evaluation universe
    assert len(branch)==7 and (branch['scenarios']==150).all()
    assert len(recurrence)==4 and (recurrence['scenarios']==150).all()
    for tbl in [branch,recurrence]:
        p=tbl.TP/(tbl.TP+tbl.FP); r=tbl.TP/(tbl.TP+tbl.FN)
        f=2*tbl.TP/(2*tbl.TP+tbl.FP+tbl.FN)
        assert np.allclose(p,tbl.precision) and np.allclose(r,tbl.recall) and np.allclose(f,tbl.F1)
    # Reconstruct a matched 30-stratum (five scenarios each) table for all methods.
    # Existing frozen BRANCHSNV/FastML/TreeTime strata are reused unchanged.
    f = frozen[frozen.scope=='full_stratum'].copy()
    f = f[['method','event_regime','tip_count','observation_condition','scenarios','TP','FP','FN']].rename(columns={'event_regime':'regime'})
    f['tip_count']=f['tip_count'].astype(int)
    p = per[(per.endpoint=='exact_latent_branch_event') & per.method.isin(['ARPIP','PAML','PastML','SNPPar'])]
    s = p.groupby(['method','regime','tip_count','observation_condition'],as_index=False)[['TP','FP','FN']].sum()
    n = p.groupby(['method','regime','tip_count','observation_condition'],as_index=False).size().rename(columns={'size':'scenarios'})
    s=s.merge(n,on=['method','regime','tip_count','observation_condition'],validate='one_to_one')
    st = pd.concat([f,s],ignore_index=True)
    assert len(st)==210 and (st.groupby('method').size()==30).all() and (st.scenarios==5).all()
    expected_keys=set(map(tuple,st[st.method=='BRANCHSNV'][['regime','tip_count','observation_condition']].values))
    for method in METHODS:
        assert set(map(tuple,st[st.method==method][['regime','tip_count','observation_condition']].values))==expected_keys
    st['precision']=np.divide(st.TP,st.TP+st.FP,out=np.full(len(st),np.nan),where=(st.TP+st.FP)!=0)
    st['recall']=np.divide(st.TP,st.TP+st.FN,out=np.full(len(st),np.nan),where=(st.TP+st.FN)!=0)
    st['F1']=np.divide(2*st.TP,2*st.TP+st.FP+st.FN,out=np.full(len(st),np.nan),where=(2*st.TP+st.FP+st.FN)!=0)
    # Validate stratum counts against the published complete pooled branch results.
    for method in METHODS:
        r=st[st.method==method][['TP','FP','FN']].sum()
        b=branch.loc[method]
        assert all(int(r[x])==int(b[x]) for x in ('TP','FP','FN')),method
    st.to_csv(OUT/'derived_210_five_scenario_strata.csv',index=False)
    return branch, recurrence, st, per, agg, boot, rec_boot


def titles(ax,tag,title,subtitle=None,title_x=0.06):
    ax.text(0.0,1.065,tag,transform=ax.transAxes,fontsize=10.4,fontweight='bold',ha='left',va='bottom',clip_on=False)
    ax.text(title_x,1.065,title,transform=ax.transAxes,fontsize=8.6,fontweight='bold',ha='left',va='bottom',clip_on=False)
    if subtitle:
        ax.text(title_x,1.018,subtitle,transform=ax.transAxes,fontsize=6.4,va='bottom',color='#555555',ha='left',clip_on=False)


def clean(ax,grid='x'):
    ax.spines[['top','right']].set_visible(False)
    if grid: ax.grid(axis=grid,color='#e9e9e9',lw=.55,zorder=0)


def consistent_jitter(keys,width=.14):
    # Stable, deterministic jitter. Keys are arbitrary strings, not RNG-dependent.
    out=[]
    for key in keys:
        h=int(hashlib.sha256(str(key).encode()).hexdigest()[:8],16)
        out.append(((h/0xffffffff)-.5)*2*width)
    return np.asarray(out)


def draw_one_tree(ax, ymid, tip1_to_parent=False):
    # Each toy tree is identical: (((G,?),(A,A))); root A, unresolved N leaf.
    # With a fixed root A, either the terminal G edge or the internal (G,?)
    # edge can carry A->G in one step if the unknown state is assigned differently.
    # Reserve a root-label gutter: text begins at the panel heading grid,
    # while the horizontal branch starts sufficiently far to its right.
    xr,xi,xt,xend=.25,.42,.58,.74
    y=[ymid+.105,ymid+.035,ymid-.035,ymid-.105]
    top=np.mean(y[:2]); bot=np.mean(y[2:]);
    strokes=[([xr,xi],[ymid,ymid]),([xi,xi],[top,bot]),([xi,xt],[top,top]),([xi,xt],[bot,bot]),([xt,xt],[y[0],y[1]]),([xt,xt],[y[2],y[3]])]
    for xs,ys in strokes:ax.plot(xs,ys,color='#333333',lw=1.15,solid_capstyle='round')
    for i in range(4):ax.plot([xt,xend],[y[i],y[i]],color='#333333',lw=1.15)
    for yy,sym in zip(y,['G','?','A','A']): ax.text(.78,yy,sym,va='center',fontsize=7.3,fontweight='semibold',color='#222222')
    ax.text(0.0,ymid-.004,'root = A',ha='left',va='center',fontsize=6.5,color='#222222')
    # Internal vs terminal eligible substitution
    xm = (xi+xt)/2 if tip1_to_parent else (xt+xend)/2
    ym = top if tip1_to_parent else y[0]
    ax.scatter([xm],[ym],s=55,marker='D',facecolor='black',edgecolor='white',lw=.5,zorder=10)
    ax.text(.88,ymid, 'shared edge' if tip1_to_parent else 'tip edge',
            ha='left',va='center',fontsize=6.4,color='#333333')


def plot_ambiguity(ax):
    ax.axis('off');ax.set_xlim(0,1);ax.set_ylim(0,1)
    titles(ax,'a','Branch-placement ambiguity', title_x=0.10)
    ax.text(.02,.90,'One site, identical observed tips',fontsize=7.2,ha='left')
    draw_one_tree(ax,.695,False)
    ax.text(.02,.495,'Equally parsimonious alternative',fontsize=7.2,ha='left')
    draw_one_tree(ax,.275,True)
    ax.text(.03,.075,'Both explain G / ? / A / A with one change.',fontsize=6.35,color='#333333')
    ax.text(.03,.028,'BRANCHSNV: do not force a unique edge.',fontsize=6.45,fontweight='bold')
    ax.text(.02,-.045,'Illustrative example; not a simulated benchmark observation.',transform=ax.transAxes,
            fontsize=6.0,color='#666666',va='top')


def plot_precision_recall(ax,branch):
    titles(ax,'b','Exact branch-event precision and recall', title_x=0.08)
    clean(ax,'both')
    ax.set_xlim(.45,.997);ax.set_ylim(.465,.875)
    # Fractions remain unchanged for all calculations and point coordinates.
    # Show percent ticks to match the F1 isolines and all other figure panels.
    ax.set_xticks([.5,.6,.7,.8,.9], labels=['50%','60%','70%','80%','90%'])
    ax.set_yticks([.50,.55,.60,.65,.70,.75,.80,.85],
                  labels=['50%','55%','60%','65%','70%','75%','80%','85%'])
    ax.set_xlabel('Precision');ax.set_ylabel('Recall')
    # iso-F1 contours
    label_xy={0.6:(0.64,0.505),0.7:(0.77,0.625),0.8:(0.79,0.792)}
    for score in (.6,.7,.8):
        p=np.linspace(.46,.99,700)
        rec=score*p/(2*p-score)
        mask=(2*p-score)>0
        valid=np.where(mask & (rec>.465)&(rec<.875))[0]
        if len(valid):
            ax.plot(p[valid],rec[valid],color='#d0d0d0',lw=.7,ls=(0,(3,3)),zorder=1)
            lx,ly=label_xy[score]
            ax.text(lx,ly,f'F1 = {int(round(score*100))}%',fontsize=5.9,color='#777777',ha='left',va='bottom',
                    bbox=dict(facecolor='white',edgecolor='none',pad=0.45,alpha=0.9))
    for method in METHODS:
        r=branch.loc[method]
        kw={'marker':MARK[method],'facecolor':GRAY[method],'edgecolor':'white', 'lw':.7,
            's':74 if method=='BRANCHSNV' else 52,'zorder':5 if method=='BRANCHSNV' else 4}
        ax.scatter([r.precision],[r.recall],**kw)
    labpos={
        'ARPIP':(.905,.853),'FastML':(.905,.822),'PAML':(.905,.791),
        'TreeTime':(.905,.760),'BRANCHSNV':(.900,.596),
        'SNPPar':(.760,.686),'PastML':(.532,.506)
    }
    for method in METHODS:
        r=branch.loc[method]
        pos=labpos[method]
        ax.annotate(method, xy=(r.precision,r.recall), xytext=pos,textcoords='data',
            fontsize=7.1 if method=='BRANCHSNV' else 6.7,
            color='#111111',fontweight='bold' if method=='BRANCHSNV' else 'normal',
            arrowprops=dict(arrowstyle='-',lw=.6,color='#a0a0a0',shrinkA=2,shrinkB=3),va='center')
    ax.text(.02,.03,'One symbol per tool; n = 150 scenarios each',transform=ax.transAxes,
            color='#555555',fontsize=6.1,va='bottom')


def draw_facet(ax, method_results, group_name, scorelookup, facet_title, methods=METHODS, dot_sizes=(8,38),
               xlim=(-2,102), show_y=False, show_x=True, has_truth=True):
    # Method-level total pooled scores, dots are matched strata or raw scenarios.
    ax.axhspan(methods.index('BRANCHSNV')-.40,methods.index('BRANCHSNV')+.40,color='#f1f1f1',zorder=0) if 'BRANCHSNV' in methods else None
    for i,m in enumerate(methods):
        group=method_results[(method_results.method==m)&(method_results.regime==group_name)]
        if not len(group): continue
        stable=consistent_jitter([f'{m}|{group_name}|{r}' for r in group.index],.155)
        ax.scatter(100*group.F1,i+stable,s=dot_sizes[0],color='#b5b5b5',alpha=.65,
                   edgecolor='none',zorder=2)
        row=scorelookup[(scorelookup.method==m)&(scorelookup.regime==group_name)]
        assert len(row)==1,(m,group_name,len(row))
        ax.scatter(100*float(row.iloc[0].F1),i,marker=MARK[m],s=dot_sizes[1],
                   edgecolor='white',lw=.5,facecolor=GRAY[m],zorder=5)
    ax.invert_yaxis()
    ax.set_yticks(np.arange(len(methods)))
    ax.set_yticklabels(methods if show_y else ['']*len(methods),fontsize=6.75)
    ax.set_xlim(*xlim)
    if show_x: ax.set_xticks([0,50,100]);ax.tick_params(axis='x',labelsize=6.1)
    else:ax.set_xticks([])
    ax.set_title(facet_title,fontsize=7.3,fontweight='semibold',pad=4)
    clean(ax,'x'); ax.tick_params(axis='y',length=0)


def save(fig, name):
    for ext in ('pdf','svg','png'):
        kwargs={'dpi':400,'facecolor':'white'}
        if ext=='pdf':
            fixed_date=datetime(2026,10,27,tzinfo=timezone.utc)
            kwargs['metadata']={'Creator':'BRANCHSNV Experiment 07 reproducible plotting',
                                'CreationDate':fixed_date,'ModDate':fixed_date}
        elif ext=='svg':
            kwargs['metadata']={'Date':'2026-10-27'}
        fig.savefig(OUT/f'{name}.{ext}',**kwargs)
    plt.close(fig)


def main_figure(branch,st,agg):
    # Explicit normalized positions: fixed print-ready geometry, no layout-engine drift.
    fig=plt.figure(figsize=(7.087,6.03),facecolor='white')
    axa=fig.add_axes([.045,.565,.38,.365]);plot_ambiguity(axa)
    axb=fig.add_axes([.515,.56,.455,.365]);plot_precision_recall(axb,branch)
    pooled=[]
    for method in METHODS:
        for regime in REGIMES:
            s=st[(st.method==method)&(st.regime==regime)][['TP','FP','FN']].sum()
            pooled.append({'method':method,'regime':regime,'F1':2*s.TP/(2*s.TP+s.FP+s.FN)})
    pooled=pd.DataFrame(pooled)
    boxes=[(.165,.152,.145,.238),(.326,.152,.145,.238),(.487,.152,.145,.238),
           (.648,.152,.145,.238),(.809,.152,.160,.238)]
    axes=[fig.add_axes(b) for b in boxes]
    for i,regime in enumerate(REGIMES):
        draw_facet(axes[i],st,regime,pooled,REGIMES_SHORT[regime],show_y=i==0,dot_sizes=(10,38))
    fig.text(.045,.445,'c',fontsize=10.4,fontweight='bold')
    fig.text(.083,.445,'Exact branch-event F1 across evolutionary regimes',fontsize=8.6,fontweight='bold')
    fig.text(.59,.106,'Pooled F1 (%)',ha='center',fontsize=7.1)
    fig.text(.045,.072,'Small grey dots: six five-scenario strata per method and regime; large symbols: pooled F1.',
             fontsize=6.7,color='#555555')
    fig.text(.045,.052,'Black diamond = BRANCHSNV; other methods have distinct marker shapes and fixed row labels.',
             fontsize=6.5,color='#555555')
    save(fig,'BRANCHSNV_Exp07_MAIN_FIGURE')


def forest(ax,boot,with_title=True):
    if with_title: titles(ax,'a','Difference in exact branch-event F1')
    clean(ax,'x')
    f=boot[boot.metric=='F1'].set_index('comparator')
    order=['ARPIP','FastML','PAML','TreeTime','SNPPar','PastML']
    for i,m in enumerate(order):
        row=f.loc[m];v=float(row.difference_vs_BRANCHSNV_pp)
        lo=float(row.CI_95_lower_pp);hi=float(row.CI_95_upper_pp)
        ax.plot([lo,hi],[i,i],color=GRAY[m],lw=1.35,zorder=3)
        ax.scatter([v],[i],s=50,marker=MARK[m],facecolor=GRAY[m],edgecolor='white',lw=.5,zorder=5)
    ax.axvline(0,color='#444444',lw=.75,ls=(0,(3,2)))
    ax.set_yticks(range(len(order)));ax.set_yticklabels(order,fontsize=7)
    ax.invert_yaxis();ax.set_xlim(-27,18)
    ax.set_xlabel('Comparator − BRANCHSNV, F1 difference (percentage points)')



def tree_size_facets(fig, st):
    """A gridded, method-row display with 10 actual stratum points per cell.

    Tree size is encoded by facet, method by fixed row and exact main-figure
    marker shape. This deliberately avoids overplotting pooled method points.
    """
    positions=[(.195,.485,.233,.215),(.462,.485,.232,.215),(.727,.485,.232,.215)]
    for i,(tip,box) in enumerate(zip((32,128,512),positions)):
        ax=fig.add_axes(box)
        ax.axhspan(METHODS.index('BRANCHSNV')-.43,
                   METHODS.index('BRANCHSNV')+.43,color='#f0f0f0',zorder=0)
        for k,method in enumerate(METHODS):
            sub=st[(st.method==method)&(st.tip_count==tip)].copy()
            assert len(sub)==10,(method,tip,len(sub))
            sub=sub.sort_values(['regime','observation_condition'])
            # One grey dot per actual five-scenario stratum (no resampling).
            jitter=consistent_jitter(
                [f'{method}|{tip}|{r.regime}|{r.observation_condition}'
                 for r in sub.itertuples(index=False)],width=.23)
            yy=k+jitter
            ax.scatter(100*sub.F1.to_numpy(), yy, s=9.5,
                       marker='o',facecolor='#bcbcbc',edgecolor='none',alpha=.78,zorder=2)
            totals=sub[['TP','FP','FN']].sum()
            f1=200*totals.TP/(2*totals.TP+totals.FP+totals.FN)
            ax.scatter([f1],[k], marker=MARK[method],s=49,
                       facecolor=GRAY[method],edgecolor='white',lw=.65,zorder=5)
        ax.set_yticks(range(len(METHODS)))
        ax.set_yticklabels(METHODS if i==0 else ['']*len(METHODS),fontsize=6.85)
        ax.tick_params(axis='y',length=0,pad=4)
        ax.set_xlim(-3,103);ax.set_xticks([0,50,100]);ax.set_ylim(-.6,len(METHODS)-.4)
        ax.invert_yaxis()
        ax.set_title(f'{tip} tips',fontsize=7.6,pad=5,fontweight='semibold')
        clean(ax,'x')
    fig.text(.578,.457,'Exact branch-event F1 (%)',ha='center',fontsize=7.0)
    fig.text(.085,.437,
             'Small grey dots: 10 five-scenario strata per method and tree size; large symbols: pooled F1.',
             ha='left',fontsize=6.45,color='#555555')


def rec_regime_panel(axarr,per,recagg):
    # Four regimes with truth-defined recurrence; UNIQUE-only excluded (zero truth)
    regimes=['parallel','convergent','reversal','mixed_recurrence']
    r=per[per.endpoint=='recurrent_site_full'].copy()
    denom=2*r.TP+r.FP+r.FN
    r['F1']=np.where(denom>0,2*r.TP/denom,np.nan)
    for ai,reg in enumerate(regimes):
        ax=axarr[ai]
        ax.set_title(REGIMES_SHORT[reg],fontsize=7.5,fontweight='semibold',pad=4)
        for i,m in enumerate(REC_METHODS):
            data=r[(r.method==m)&(r.regime==reg)]
            assert len(data)==30
            ys=i+consistent_jitter(data['scenario_id'],.16)
            ax.scatter(data['F1']*100,ys,s=6.5,color='#bdbdbd',alpha=.68,lw=0,zorder=2)
            pooled=recagg[(recagg.method==m)&(recagg.regime==reg)&(recagg.endpoint=='recurrent_site_full')]
            assert len(pooled)==1
            ax.scatter(100*float(pooled.iloc[0].F1),i,s=42,marker=MARK[m],facecolor=GRAY[m],
                       edgecolor='white',lw=.5,zorder=6)
        ax.set_ylim(-.55,3.55);ax.invert_yaxis()
        ax.set_yticks(range(4));ax.set_yticklabels(REC_METHODS if ai==0 else ['']*4,fontsize=7)
        ax.set_xlim(-10,105);ax.set_xticks([0,50,100]);ax.tick_params(axis='x',labelsize=6.3)
        ax.tick_params(axis='y',length=0)
        clean(ax,'x')
    # Shared xlabel is placed by the parent figure to avoid repeating axis labels.



def denom_sensitivity(ax,rec,agg,with_title=True):
    if with_title: titles(ax,'d','Endpoint eligibility changes POUTINE F1')
    clean(ax,'x')
    a=rec.loc['POUTINE']
    b=agg[(agg.method=='POUTINE')&(agg.endpoint=='recurrent_site_observed_biallelic_only')&(agg.regime=='all')].iloc[0]
    ys=[1,0]; vals=[100*a.F1,100*b.F1]
    ax.plot(vals,ys,color='#777777',lw=1.2,zorder=1)
    # POUTINE retains the star marker used in the main-figure method key.
    # Filled vs open indicates a change in evaluation denominator, not tool.
    for x,y in zip(vals,ys):ax.scatter([x],[y],s=90,marker=MARK['POUTINE'],facecolor='#222222' if y else 'white',edgecolor='#111111',lw=.8,zorder=3)
    ax.set_yticks([0,1]);ax.set_yticklabels(['Observed biallelic only','All recurrent sites'],fontsize=7)
    ax.set_xlim(40,75);ax.set_xticks([40,50,60,70]);ax.set_xlabel('POUTINE pooled F1 (%)')
    ax.set_ylim(-.6,1.55)
    ax.text(vals[0]+1.0,1,f'{vals[0]:.1f}%',va='center',fontsize=7.3)
    ax.text(vals[1]+1.0,0,f'{vals[1]:.1f}%',va='center',fontsize=7.3)



def supp_figure(branch, rec, st, per, agg, boot):
    # Full-width stacked panels on a fixed 180-mm grid: one left margin for
    # a, b, c and d. This also gives tree-size points their own method rows.
    fig=plt.figure(figsize=(7.087,9.00),facecolor='white')
    left_tag=.055
    left_title=.085
    def section(y,tag,title):
        fig.text(left_tag,y,tag,fontsize=10.4,fontweight='bold',ha='left',va='baseline')
        fig.text(left_title,y,title,fontsize=8.6,fontweight='bold',ha='left',va='baseline')

    section(.970,'a','Difference in exact branch-event F1')
    axa=fig.add_axes([.195,.803,.755,.131])
    forest(axa,boot,with_title=False)

    section(.724,'b','Variation across tree sizes')
    tree_size_facets(fig,st)

    # Deliberate paragraph-like white gap after panel b note and above panel c.
    section(.391,'c','Recurrent-site detection: individual scenarios and pooled scores')
    cboxes=[(.195,.225,.174,.123),(.392,.225,.174,.123),
            (.589,.225,.174,.123),(.786,.225,.174,.123)]
    regaxes=[fig.add_axes(b) for b in cboxes]
    rec_regime_panel(regaxes,per,agg)
    fig.text(.578,.188,'Recurrent-site F1 (%)',ha='center',fontsize=7.0)
    fig.text(.085,.164,'Small dots: 30 individual scenarios per method and regime; large symbols: pooled F1.',
             ha='left',fontsize=6.45,color='#555555')
    fig.text(.085,.147,'Unique-only: no recurrent truth sites (F1 undefined). Reversal: zero recovered sites.',
             ha='left',fontsize=6.3,color='#555555')

    section(.117,'d','Endpoint eligibility changes POUTINE F1')
    denom_sensitivity(fig.add_axes([.276,.035,.64,.066]),rec,agg,with_title=False)

    save(fig,'BRANCHSNV_Exp07_SUPPLEMENTARY_FIGURE')


def write_notes(branch,rec):
    (HERE/'FIGURE_LEGENDS.md').write_text('''# Experiment 07 assembled figure legends

## Main figure | Conditional branch-event recovery across 150 simulated scenarios
**a**, Schematic illustration of alternative, equally parsimonious placements of an A→G substitution at a nucleotide site with one unresolved terminal state. Neither illustrated tree was sampled from Experiment 07; the example explains why BRANCHSNV retains branch-placement ambiguity rather than assigning a definite change to one focal edge. **b**, Pooled exact branch-event precision and recall for BRANCHSNV and six external tools (150 matched scenarios for each, 9,600 latent truth events per method). Each symbol represents one method; dashed curves indicate constant F1 scores. **c**, Exact branch-event F1 by mutation regime. Large method-shaped symbols depict pooled F1 over 30 scenarios, while six small grey dots per method and regime give the observed F1 for each matched five-scenario stratum (3 tree sizes × 2 observation conditions). Source: checksum-verified original three-method scoring and completed six-tool scoring extension. Branch lengths provided to comparators were derived from realised simulated events; these results therefore measure latent-history recovery conditional on those supplied branch lengths rather than performance under independently generated branch lengths. Missing and placement-ambiguous branch assignments are not assumed to be correct calls.

## Supplementary figure | Heterogeneity, paired contrasts and recurrence-endpoint eligibility
**a**, Differences in pooled exact branch-event F1 between each of the six external comparators and BRANCHSNV. Points show observed differences in percentage points and horizontal lines the previously calculated 95% bootstrap confidence intervals from regime-balanced resampling of 30 matched five-scenario strata (25,000 replicates). **b**, Exact branch-event F1 by phylogeny size in three separate facets; each method occupies a fixed row. Small points denote the 10 five-scenario stratum results per method and tree size (5 mutation regimes × 2 observation conditions); larger method-shaped symbols show the pooled score across 50 scenarios. **c**, Recurrent-site F1 by mutation regime for TreeTime, SNPPar, HomoplasyFinder and POUTINE. Small points represent individual scenario F1 scores (30 per method and eligible regime); larger symbols are pooled estimates across all 30 scenarios in each regime. The unique-only regime has no recurrent truth sites and is omitted because F1 is undefined, not perfect; reversal scenarios contain recurrent truth sites but none were detected. The recurrence endpoint is distinct from the exact branch-event endpoint. **d**, POUTINE F1 (star markers as in the main-figure marker key) under full recurrent-site scoring versus the observed-biallelic-only eligibility restriction; these scores have different denominators, so the restricted value must not be interpreted as improved accuracy on a fixed evaluation set.

### Plotting and reproducibility
All numerical panels derive exclusively from the source archive with SHA256 checks. The only conceptual panel is main figure **a**, drawn deterministically by the same Python script. Grayscale and symbol shape redundantly encode method identity; the symbols, direct labels and fixed row order are sufficient for monochrome printing. No bar plots or manually invented uncertainty intervals are used.
''')
    (HERE/'README.md').write_text('''# BRANCHSNV Experiment 07 — final assembled figures

**Primary outputs**
- `figures/BRANCHSNV_Exp07_MAIN_FIGURE.pdf` / `.svg` / `.png`
- `figures/BRANCHSNV_Exp07_SUPPLEMENTARY_FIGURE.pdf` / `.svg` / `.png`
- `FIGURE_LEGENDS.md`

**Regenerate exactly** (Python 3.10+):

```bash
python -m pip install "numpy>=1.24" "pandas>=2.0" "matplotlib>=3.7"
python plot_final_figures.py
```

The script hashes `BRANCHSNV_Experiment07_FINAL_RESULTS.tar.gz` against its fixed SHA256, extracts the original six source files, verifies `SHA256SUMS`, validates pooled counts and reproduces the main and supplementary figures. Precomputed paired bootstrap intervals (25,000 resamples) are supplied in `paired_stratum_bootstrap_differences.csv`; they are plotted exactly, not regenerated with a new seed. The original source archive and intervals are included here.

The main figure's conceptual four-tip ambiguity illustration is not an empirical observation. All numerical marks come from checksum-verified outputs. All supplementary panel headers share the same fixed left edge. The tree-size panel uses separate facets and one fixed row per method, showing all 10 five-scenario-stratum results per cell and the pooled result without overlap. The markers for every tool are defined by the same MARK dictionary used in the main figure (POUTINE also uses its star in the endpoint panel). Grayscale, redundant marker shapes and fixed row ordering ensure monochrome legibility; vector PDFs/SVGs contain text and editable vector elements.

Note: this figure set is a designed publication candidate. Final editorial placement and journal artwork requirements should be checked against the submission system. Do not label repeated matched-stratum dots as independently replicated datasets.
''')


def main():
    data=read()
    main_figure(data[0],data[2],data[4])
    supp_figure(data[0],data[1],data[2],data[3],data[4],data[5])
    write_notes(data[0],data[1])
    print('FINAL_ASSEMBLED_FIGURES=PASS')
    print('SOURCE_SHA256=',EXPECTED_ARCHIVE_SHA)
    print('METHOD_COUNT=7, RECURRENT_METHOD_COUNT=4, SCENARIOS=150, STRATA=30_PER_METHOD')

if __name__=='__main__':main()

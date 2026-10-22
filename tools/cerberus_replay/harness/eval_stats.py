import sys; sys.path.insert(0,'.')
import collections, math
import numpy as np
from scipy.stats import rankdata
import cerberus_replay as C, engine_run as E, metrics as M
FAST=("yield_curve_10y3m","yield_curve_10y2y","hy_oas","ig_oas","credit_stress_hyg_lqd","breadth_rsp_spy",
      "copper_gold","cboe_skew","vix_level","vix_term_structure","spx_vs_200dma","real_rate_10y_tips")
def auc(pos,neg):
    if not len(pos) or not len(neg): return float('nan')
    r=rankdata(np.concatenate([pos,neg])); n1,n0=len(pos),len(neg)
    return (r[:n1].sum()-n1*(n1+1)/2)/(n1*n0)
def stats_for(rows,d,T=0.9):
    r=rows[d]; sn=r['snap']
    if not sn: return None
    fast=[(i,s) for i,(v,s) in sn.items() if i in FAST]
    out=dict(breadth=r['breadth'],
             count_v1=r['cnt'].count if r['cnt'] else None,
             acute_avail=max(r['masters'].values()) if r['masters'] else None,
             vol=r['masters'].get('volatility_master'), curve=r['masters'].get('curve_master'),
             fin=r['masters'].get('financial_conditions_master'),credit=r['masters'].get('credit_master'))
    if fast:
        w=[C.TIER_W[C.TIER[i]] for i,_ in fast]; out['fast_breadth']=sum(wi*s for wi,(_,s) in zip(w,fast))/sum(w)
        for T_ in (0.7,0.8,0.9): out[f'fastcnt{int(T_*100)}']=sum(1 for _,s in fast if s>=T_)
        out['fast_n']=len(fast)
        for T_ in (0.7,0.8,0.9): out[f'fastfrac{int(T_*100)}']=out[f'fastcnt{int(T_*100)}']/len(fast)
    return out
if __name__=="__main__":
    P=C.Panel(); rows=E.build_rows(P); lab=M.label_days(P,C.forward_labels(P))
    tab={d:stats_for(rows,d) for d in P.days}
    keys=["breadth","count_v1","acute_avail","vol","curve","fin","credit","fast_breadth","fastcnt70","fastcnt80","fastcnt90","fastfrac70","fastfrac80","fastfrac90"]
    print("DAY-LEVEL AUC (pos = >=20%/126d or >=15%/63d forward fall; neg = fully-observed no-event days). 0.5 = no skill.")
    print("NOTE days are serially dependent; effective n ~ number of episodes. Descriptive, not inferential.\n")
    print("stat           | ALL    | "+" | ".join(f"{e[0]:>8s}" for e in C.EPISODES if e[0] in ("2000-02","2007-09","2011","2022")))
    for k in keys:
        def sel(ep=None):
            pos=[tab[d][k] for d in P.days if lab[d]=='pos' and tab[d] and tab[d].get(k) is not None and (ep is None or P.win[d]==ep)]
            neg=[tab[d][k] for d in P.days if lab[d]=='neg' and tab[d] and tab[d].get(k) is not None and (ep is None or P.win[d]==ep)]
            return np.array(pos,float),np.array(neg,float)
        a=auc(*sel()); parts=[auc(*sel(e)) for e in ("2000-02","2007-09","2011","2022")]
        npos,nneg=len(sel()[0]),len(sel()[1])
        print(f"{k:14s} | {a:.3f}  | "+" | ".join(f"{x:8.3f}" for x in parts)+f"   (n_pos {npos}, n_neg {nneg})")

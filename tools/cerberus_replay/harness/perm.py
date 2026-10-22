import sys; sys.path.insert(0,'.')
import collections
import numpy as np
import cerberus_replay as C, engine_run as E
def fwd_table(panel, h=126):
    """per day: (fwd min return, fwd end return, fully observed) over h trading days inside the window"""
    days=panel.days; idx={d:i for i,d in enumerate(days)}; out={}
    for d in days:
        i=idx[d]; w=panel.win[d]; p0=panel.spx[d]; fut=[]
        for j in range(i+1,min(i+1+h,len(days))):
            if panel.win[days[j]]!=w: break
            fut.append(panel.spx[days[j]]/p0-1)
        out[d]=(min(fut) if fut else None, fut[-1] if fut else None, len(fut)==h)
    return out
def permission_table(states, fwd, permitted=("CALM","RECOVERY")):
    g=collections.defaultdict(list)
    for d,s in states.items():
        mn,en,full=fwd[d]
        if not full: continue
        g["PERMIT" if s["state"] in permitted else "DENY"].append((mn,en))
    out={}
    for k,v in g.items():
        mn=np.array([a for a,_ in v]); en=np.array([b for _,b in v])
        out[k]=dict(n=len(v),p10=float((mn<=-0.10).mean()),p15=float((mn<=-0.15).mean()),p20=float((mn<=-0.20).mean()),
                    mean_min=float(mn.mean()),mean_end=float(en.mean()))
    return out
def show(name,tab):
    for k in ("PERMIT","DENY"):
        r=tab.get(k)
        if r: print(f"  {name:22s} {k:6s} n={r['n']:4d}  P(fwd126 min<=-10%)={r['p10']:.2f}  <=-15%={r['p15']:.2f}  <=-20%={r['p20']:.2f}  mean fwd-min {r['mean_min']:+.1%}  mean fwd-ret {r['mean_end']:+.1%}")
if __name__=="__main__":
    P=C.Panel(); rows=E.build_rows(P); fw=fwd_table(P)
    allfull=[v for v in fw.values() if v[2]]
    mn=np.array([a for a,_,_ in allfull]); print("UNCONDITIONAL (all fully-observed days):",len(mn),f"P(<=-10%)={(mn<=-.1).mean():.2f} P(<=-15%)={(mn<=-.15).mean():.2f} P(<=-20%)={(mn<=-.2).mean():.2f}")
    V1=E.run_machine(rows,P.days,E.Params()); show("V1 deployed (avail)",permission_table(V1,fw))

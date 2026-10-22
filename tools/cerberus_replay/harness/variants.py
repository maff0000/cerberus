import sys; sys.path.insert(0,'.')
import copy, collections
import numpy as np
import cerberus_replay as C, engine_run as E, metrics as M, perm as PM
def calib_rows(rows):
    """CALIBRATION MODE (replay-only): volatility_master = max of the components that exist (live has VIX3M always).
       Everything else untouched.  Never used for the 'as deployed' verdict."""
    r2={}
    for d,r in rows.items():
        r=dict(r); r['masters']=dict(r['masters'])
        sn=r['snap']
        if 'vix_level' in sn:
            r['masters']['volatility_master']=max(sn[i][1] for i in ('vix_level','vix_term_structure') if i in sn)
        r2[d]=r
    return r2
def summarize(name,P,rows,params,fw,lab):
    st=E.run_machine(rows,P.days,params)
    perm=PM.permission_table(st,fw)
    t=M.day_table(st,lab,P); s=M.summarise(t)
    share=collections.Counter(v['state'] for v in st.values())
    n=len(st)
    p,d=perm.get('PERMIT'),perm.get('DENY')
    print(f"{name:34s} ALARM {share['ALARM']/n:5.1%} WATCH {share['WATCH']/n:5.1%} CALM {share['CALM']/n:5.1%} | "
          f"P(fwd<=-20%|PERMIT) {p['p20']:.2f} vs DENY {d['p20']:.2f} | P(<=-10%) {p['p10']:.2f} vs {d['p10']:.2f} | deny-recall {s['recall_deny']:.2f} alarm-recall {s['recall_alarm']:.2f}")
    return st
if __name__=="__main__":
    P=C.Panel(); rows=E.build_rows(P); fw=PM.fwd_table(P); lab=M.label_days(P,C.forward_labels(P))
    cr=calib_rows(rows)
    summarize("M0 deployed, avail masters",P,rows,E.Params(),fw,lab)
    summarize("M1 + vol VIX-only pre-2009",P,cr,E.Params(),fw,lab)
    summarize("M2 M1, vol stress .70",P,cr,E.Params(stress={'volatility_master':.70}),fw,lab)
    summarize("M2b M1, vol stress .60",P,cr,E.Params(stress={'volatility_master':.60}),fw,lab)
    summarize("M3 M2, breadth limb OFF",P,cr,E.Params(stress={'volatility_master':.70},b_mid=9),fw,lab)
    summarize("M4 M3, curve warn .80",P,cr,E.Params(stress={'volatility_master':.70},b_mid=9,warn={'curve_master':.80}),fw,lab)
    summarize("M5 M3, curve warn .70",P,cr,E.Params(stress={'volatility_master':.70},b_mid=9,warn={'curve_master':.70}),fw,lab)
    summarize("M6 M3, vol warn .5",P,cr,E.Params(stress={'volatility_master':.70},b_mid=9,warn={'volatility_master':.50}),fw,lab)

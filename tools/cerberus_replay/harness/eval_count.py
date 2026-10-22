import sys; sys.path.insert(0,'.')
import collections, numpy as np
import cerberus_replay as C, engine_run as E, metrics as M, perm as PM, variants as V, protect as PR
FAST2=("yield_curve_10y3m","yield_curve_10y2y","hy_oas","ig_oas","copper_gold","cboe_skew","vix_level","vix_term_structure","spx_vs_200dma","real_rate_10y_tips")  # market-priced, daily, minus the two defective ratios
def with_count(rows,T,k,fast=FAST2,frac=False):
    out={}
    for d,r in rows.items():
        r=dict(r); r['masters']=dict(r['masters']); sn=r['snap']
        con=[(i,s) for i,(v,s) in sn.items() if i in fast]
        if con:
            n=sum(1 for _,s in con if s>=T)
            r['cv2']=n; r['cv2n']=len(con)
            hit=(n/len(con)>=k) if frac else (n>=k)
            r['masters']['count_v2']=1.0 if hit else 0.0
        out[d]=r
    return out
if __name__=="__main__":
    P=C.Panel(); rows=E.build_rows(P); cr=V.calib_rows(rows); fw=PM.fwd_table(P); lab=M.label_days(P,C.forward_labels(P))
    base=dict(stress={'volatility_master':.70})
    print("distribution of fast count (T=.8) when considered>=6: pos vs neg days")
    c=with_count(cr,.8,99)
    for L in ('pos','neg'):
        v=[c[d]['cv2'] for d in P.days if lab[d]==L and 'cv2' in c[d] and c[d]['cv2n']>=6]
        print(" ",L,len(v),dict(sorted(collections.Counter(v).items())))
    print("\nstanding ALARM from count_v2>=k (T=.8) IN ADDITION to vol .70 stress; persistence 5")
    print("k | ALARM% DENY% | P(fwd<=-20%|PERMIT) vs DENY | share-ahead primary / all8 | episodes signalled")
    P0=E.Params(**base)
    st=E.run_machine(cr,P.days,P0); r=PR.protection(P,st); prim=[x for x in r if x[6]<=-.2]
    print(f"- (none) | {sum(1 for v in st.values() if v['state']=='ALARM')/len(st):.1%} {sum(1 for v in st.values() if v['state']!='CALM')/len(st):.1%} | {PM.permission_table(st,fw)['PERMIT']['p20']:.2f} vs {PM.permission_table(st,fw)['DENY']['p20']:.2f} | {sum(x[5] for x in prim)/len(prim):.0%} / {sum(x[5] for x in r)/len(r):.0%} | {sum(1 for x in r if x[3])}/8")
    for k in (2,3,4,5):
        cc=with_count(cr,.8,k)
        st=E.run_machine(cc,P.days,E.Params(**base)); r=PR.protection(P,st); prim=[x for x in r if x[6]<=-.2]
        pt=PM.permission_table(st,fw)
        print(f"{k} | {sum(1 for v in st.values() if v['state']=='ALARM')/len(st):.1%} {sum(1 for v in st.values() if v['state']!='CALM')/len(st):.1%} | {pt['PERMIT']['p20']:.2f} vs {pt['DENY']['p20']:.2f} | {sum(x[5] for x in prim)/len(prim):.0%} / {sum(x[5] for x in r)/len(r):.0%} | {sum(1 for x in r if x[3])}/8")

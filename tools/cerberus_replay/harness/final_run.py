import sys; sys.path.insert(0,'.')
import collections, json, datetime as dt
import numpy as np
import cerberus_replay as C, engine_run as E, metrics as M, perm as PM, variants as V, protect as PR, eval_count as EC
P=C.Panel(); rows=E.build_rows(P); cr=V.calib_rows(rows); fw=PM.fwd_table(P); lab=M.label_days(P,C.forward_labels(P))
REC=dict(stress={'volatility_master':.70}, warn={'curve_master':.80}, b_mid=9, b_high=9)      # R: recommended
REC_CNT=EC.with_count(cr,.8,2)
cfg={
 "A_deployed_live_strict":(rows,E.Params(strict_unknown=True)),
 "B_deployed_avail_masters":(rows,E.Params()),
 "C_recommended_masters_only":(cr,E.Params(**REC)),
 "D_recommended_plus_count_v2_k2":(REC_CNT,E.Params(**REC)),
}
out={}
for name,(rw,pm) in cfg.items():
    st=E.run_machine(rw,P.days,pm)
    n=len(st); sh=collections.Counter(v['state'] for v in st.values())
    pt=PM.permission_table(st,fw)
    pa=PR.protection(P,st); pd=PR.protection(P,st,("WATCH","ALARM"))
    prim=[x for x in pa if x[6]<=-.2]; primd=[x for x in pd if x[6]<=-.2]
    t=M.day_table(st,lab,P); s=M.summarise(t)
    out[name]=dict(share={k:round(v/n,4) for k,v in sh.items()},
        permit_p20=pt.get('PERMIT',{}).get('p20'),deny_p20=pt.get('DENY',{}).get('p20'),
        permit_p10=pt.get('PERMIT',{}).get('p10'),deny_p10=pt.get('DENY',{}).get('p10'),
        n_permit=pt.get('PERMIT',{}).get('n'),n_deny=pt.get('DENY',{}).get('n'),
        alarm_ahead_primary=sum(x[5] for x in prim)/len(prim),alarm_ahead_all=sum(x[5] for x in pa)/len(pa),
        deny_ahead_primary=sum(x[5] for x in primd)/len(primd),deny_ahead_all=sum(x[5] for x in pd)/len(pd),
        alarm_signalled=sum(1 for x in pa if x[3]),per_episode=[(x[0],str(x[3]) if x[3] else None,None if x[4] is None else round(x[4],3),round(x[5],3)) for x in pa],
        neg_days_alarm=s['fpr_alarm'],neg_days_deny=s['fpr_deny'],pos_days_alarm=s['recall_alarm'],pos_days_deny=s['recall_deny'])
json.dump(out,open("../out/results.json","w"),indent=1,default=str)
for k,v in out.items():
    print(f"\n{k}: states {v['share']}")
    print(f"   PERMIT n={v['n_permit']} P(fwd126<=-20%)={v['permit_p20']} P(<=-10%)={v['permit_p10']} | DENY n={v['n_deny']} P20={v['deny_p20']} P10={v['deny_p10']}")
    print(f"   share of decline ahead at first ALARM: primary {v['alarm_ahead_primary']:.0%}, all8 {v['alarm_ahead_all']:.0%}; at first DENY: primary {v['deny_ahead_primary']:.0%}, all8 {v['deny_ahead_all']:.0%}; ALARM signalled {v['alarm_signalled']}/8")
    print(f"   labelled days: ALARM on pos {v['pos_days_alarm']:.2f}, on neg {v['neg_days_alarm']:.2f} | DENY on pos {v['pos_days_deny']:.2f}, on neg {v['neg_days_deny']:.2f}")
    print("   per-episode first ALARM / DD then / share ahead:",[(e,d,dd,a) for e,d,dd,a in v['per_episode']])

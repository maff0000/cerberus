import sys; sys.path.insert(0,'.')
import collections, numpy as np
import cerberus_replay as C, engine_run as E, perm as PM, variants as V
P=C.Panel(); rows=E.build_rows(P); cr=V.calib_rows(rows); fw=PM.fwd_table(P)
st=E.run_machine(cr,P.days,E.Params(stress={'volatility_master':.70}))
# acute series per window
acute={d:(max(cr[d]['masters'].values()) if cr[d]['masters'] else None) for d in P.days}
print("acute_rising = acute > acute L readings ago (strict; deployed form has no deadband). Evaluated on PERMITTED days (CALM|RECOVERY) only:")
print("L  | rising share of permitted days | P(fwd126 min<=-10%) rising vs not | P(<=-20%) rising vs not | mean fwd-min rising vs not")
for L in (5,10,20,40):
    g=collections.defaultdict(list)
    cur=None;h=[]
    for d in P.days:
        if P.win[d]!=cur: cur=P.win[d];h=[]
        a=acute[d]
        if a is not None and len(h)>=L and st[d]['state'] in ('CALM','RECOVERY') and fw[d][2]:
            g['rise' if a>h[-L]+1e-12 else 'flat'].append(fw[d][0])
        if a is not None: h.append(a)
    r,f=np.array(g['rise']),np.array(g['flat'])
    print(f"{L:2d} | {len(r)/(len(r)+len(f)):.0%} ({len(r)}/{len(r)+len(f)}) | {(r<=-.1).mean():.2f} vs {(f<=-.1).mean():.2f} | {(r<=-.2).mean():.2f} vs {(f<=-.2).mean():.2f} | {r.mean():+.1%} vs {f.mean():+.1%}")

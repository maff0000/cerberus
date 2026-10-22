import sys; sys.path.insert(0,'.')
import datetime as dt, statistics as st
import numpy as np
import single_master as SM, eval_master as EM, engine_run as E, cerberus_replay as C
spx=EM.spx
days,s=SM.score_series("vol")
alld=sorted(spx); vals=[spx[d] for d in alld]; cs=np.cumsum([0]+vals); ma={}
for i,d in enumerate(alld):
    if i>=199: ma[d]=(cs[i+1]-cs[i-199])/200
idx={d:i for i,d in enumerate(alld)}
def trend(d,tol=-0.0025):
    i=idx[d]
    if d not in ma or i<219: return False
    prev=ma.get(alld[i-20]); return prev is not None and spx[d]>ma[d] and ma[d]/prev-1>=tol
tr={d:trend(d) for d in days}
def run(lock,use_trend,stress=.70,exit_=.5):
    rows={d:dict(w="all",breadth=None,masters={"vol":s[d]},unknown=(),snap={}) for d in days}
    p=E.Params(warn={"vol":.6},stress={"vol":stress},exit={"vol":exit_},eligible={"vol":True},b_mid=9,b_high=9,trend=tr if use_trend else None,lock=lock)
    return E.run_machine(rows,days,p)
def report(name,stt):
    reo=[];late=[]
    for p,t in EM.EPIS:
        for a,b in zip(days,days[1:]):
            if p<=b<=t and stt[a]['state'] in('WATCH','ALARM') and stt[b]['state'] in ('CALM','RECOVERY') and any(stt[x]['state']=='ALARM' for x in days if b-dt.timedelta(days=30)<=x<b):
                reo.append(spx[t]/spx[b]-1)
        perm=[d for d in days if d>=t and stt[d]['state'] in ('CALM','RECOVERY')]
        # first permit after trough that is preceded by a deny within 60d before trough..
        if perm: late.append(((perm[0]-t).days,spx[perm[0]]/spx[t]-1))
    deny=sum(1 for d in days if stt[d]['state'] in('WATCH','ALARM'))/len(days)
    yrs=(days[-1]-days[0]).days/365.25
    # opportunity: deny days outside any decline window (peak-60d .. trough+250d)
    def near(d): return any(p-dt.timedelta(days=60)<=d<=t+dt.timedelta(days=250) for p,t in EM.EPIS)
    out_deny=sum(1 for d in days if stt[d]['state'] in('WATCH','ALARM') and not near(d))
    print(f"{name:34s} premature re-opens {len(reo)} (mean further fall {st.mean(reo) if reo else 0:+.0%}) | re-entry after trough: median {st.median(l[0] for l in late):.0f}d / {st.median(l[1] for l in late):+.0%} off low, max {max(l[0] for l in late)}d | DENY {deny:.1%} of days, {out_deny} deny-days outside decline±250d ({out_deny/yrs:.0f}/yr)")
report("deployed machine (no lock)",run(False,False))
report("lock, trend=flattening 200dma",run(True,True))
report("lock, trend=none (permanent lock!)",run(True,False))

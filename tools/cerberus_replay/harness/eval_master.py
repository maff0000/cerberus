import sys; sys.path.insert(0,'.')
import datetime as dt, collections
import single_master as SM, control as K, cerberus_replay as C
x=SM.data(); spx=x['spx']
alld=[d for d in sorted(spx) if d>=dt.date(1990,1,2)]
dec=SM.zigzag_declines(alld,spx); EPIS=SM.clusters(dec)
def crossing(p,t,lvl=-0.10):
    for d in alld:
        if p<=d<=t and spx[d]/spx[p]-1<=lvl: return d
    return None
def evaluate(days,states,epis=EPIS,pre=60,post=30):
    A=SM.spans(states,days,("ALARM",)); W=SM.spans(states,days,("WATCH","ALARM"))
    res=[]
    for p,t in epis:
        if p<days[0]: continue
        c10=crossing(p,t); dd=spx[t]/spx[p]-1
        hit=[s for s in A if s[1]>=p-dt.timedelta(days=pre) and s[0]<=t]
        hitw=[s for s in W if s[1]>=p-dt.timedelta(days=pre) and s[0]<=t]
        first=min((max(s[0],p-dt.timedelta(days=pre)) for s in hit),default=None)
        firstw=min((max(s[0],p-dt.timedelta(days=pre)) for s in hitw),default=None)
        res.append(dict(p=p,t=t,dd=dd,c10=c10,alarm=first,
                        lead=(c10-first).days if first and c10 else None,
                        avoid=(spx[t]/spx[first]-1) if first and first<=t else None,
                        watch=firstw, wlead=(c10-firstw).days if firstw and c10 else None))
    def inep(s):
        return any(s[1]>=p-dt.timedelta(days=pre) and s[0]<=t+dt.timedelta(days=post) for p,t in epis)
    fa=[s for s in A if not inep(s)]; faw=[s for s in W if not inep(s)]
    yrs=(days[-1]-days[0]).days/365.25
    return dict(res=res,alarm_days=sum(1 for d in days if states[d]['state']=='ALARM')/len(days),
                deny_days=sum(1 for d in days if states[d]['state'] in('WATCH','ALARM'))/len(days),
                fa_spans=len(fa),fa_per_yr=len(fa)/yrs,fa_days=sum((s[1]-s[0]).days+1 for s in fa),
                faw_spans=len(faw),faw_per_yr=len(faw)/yrs, spans=A, fa=fa)
if __name__=="__main__":
    print("EPISODES (zigzag15 clusters, gap<200d merged):")
    for p,t in EPIS: print("  ",p,"->",t,f"{spx[t]/spx[p]-1:+.1%}","c10",crossing(p,t))
    days,s=SM.score_series("vol")
    print("\nVOL master (VIX level; +VIX/VIX3M from 2006-07), 1990-2026, persistence 5, exit .5")
    print("stress warn | ALARM%  DENY% | FA spans (/yr)  | caught-before-10%dd / caught-at-all / of N | median lead d | mean avoided")
    for stress in (0.5,0.6,0.7,0.8,0.85,0.9,1.0):
        for warn in (0.4,0.6):
            if warn>=stress: continue
            st=SM.run(days,s,"vol",warn,stress,0.5)
            r=evaluate(days,st)
            R=[e for e in r['res']]
            before=sum(1 for e in R if e['lead'] is not None and e['lead']>0)
            anyc=sum(1 for e in R if e['alarm'] is not None)
            leads=sorted(e['lead'] for e in R if e['lead'] is not None)
            av=[e['avoid'] for e in R if e['avoid'] is not None]
            print(f" {stress:.2f} {warn:.2f} | {r['alarm_days']*100:5.1f}% {r['deny_days']*100:5.1f}% | {r['fa_spans']:3d} ({r['fa_per_yr']:.2f}) fa_days {r['fa_days']:4d} | {before}/{anyc}/{len(R)} | {leads[len(leads)//2] if leads else None} | {sum(av)/len(av) if av else float('nan'):+.1%}")

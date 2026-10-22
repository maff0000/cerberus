import sys; sys.path.insert(0,'.')
import datetime as dt, collections
import single_master as SM, eval_master as EM, cerberus_replay as C
spx=EM.spx
days,s=SM.curve_series()
print("CURVE master (max of 10y3m, 10y2y scores), 1990-2026: share of days by score bucket and by year at >=warning")
by=collections.defaultdict(lambda:[0,0])
for d in days:
    by[d.year][1]+=1
    if s[d]>=0.6: by[d.year][0]+=1
print(" years with >=25% of days at/above warning(.6):",{y:f"{a/b:.0%}" for y,(a,b) in sorted(by.items()) if a/b>=0.25})
print("\nWATCH-only curve master (warn varied, stress irrelevant=ineligible): lead to peak, deny share, WATCH spans")
print("warn | WATCH% of days | per episode: first WATCH entry relative to S&P peak (days before peak; + = early) ")
for warn in (0.5,0.6,0.7,0.8):
    st=SM.run(days,s,"curve",warn,0.85,0.5,eligible=False)
    W=SM.spans(st,days,("WATCH",)); wd=sum(1 for d in days if st[d]['state']=='WATCH')/len(days)
    out=[]
    for p,t in EM.EPIS:
        # latest WATCH span that starts before the peak and reaches the peak or later (i.e. warning in force at the peak)
        cand=[w for w in W if w[0]<=p+dt.timedelta(days=0) and w[1]>=p-dt.timedelta(days=0)]
        if cand: out.append(f"{p.year}:{(p-cand[0][0]).days}d")
        else:
            later=[w for w in W if p<w[0]<=t]
            out.append(f"{p.year}:{'late +'+str((later[0][0]-p).days)+'d' if later else 'none'}")
    print(f" {warn:.2f} | {wd:5.1%} | "+"  ".join(out))

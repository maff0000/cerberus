import sys, os, json, collections, datetime as dt
SP=os.environ["R2_SCRATCH"]; sys.path.insert(0, os.path.join(SP,"harness"))
import cerberus_replay as C
D=dt.date.fromisoformat
P=C.Panel()
R={}
for ep,_,_ in C.EPISODES:
    for l in open(f"{SP}/live/runs/C_avail_liveshaped/{ep}.jsonl"):
        r=json.loads(l); R[D(r['date'])]=r
STRESS={"credit_master":.85,"volatility_master":.70,"financial_conditions_master":.85}
days=P.days; idx={d:i for i,d in enumerate(days)}
def fwd(d,h=63):
    i=idx[d]; w=P.win[d]; p0=P.spx[d]; fut=[P.spx[days[j]]/p0-1 for j in range(i+1,min(i+1+h,len(days))) if P.win[days[j]]==w]
    return (min(fut) if fut else None, len(fut)==h)
tab=collections.defaultdict(list)
for d in days:
    e=R[d].get('equity_crash') or {}
    if e.get('cand')!='state.alarm': continue
    ms=e.get('masters') or {}
    if any(v>=STRESS.get(m,9) for m,v in ms.items()): continue
    tab[(P.win[d], tuple(e['at_or_beyond']))].append(d)
print("count-only ALARM-candidate days by window and the indicators at/beyond 0.80:")
for (w,k),ds in sorted(tab.items(), key=lambda kv:(kv[0][0],kv[1][0])):
    fm=[a for a,full in (fwd(d) for d in ds) if a is not None]
    dd=sorted(P.spx[d]/max(P.spx[x] for x in days if P.win[x]==w and x<=d)-1 for d in ds)
    print(f"  {w:9s} {len(ds):3d}d {ds[0]}..{ds[-1]}  {list(k)}  S&P dd-from-window-peak median {dd[len(dd)//2]:+.1%}; 63d fwd-min median {sorted(fm)[len(fm)//2]:+.1%}" if fm else f"  {w} {len(ds)}d {ds[0]}..{ds[-1]} {list(k)}")

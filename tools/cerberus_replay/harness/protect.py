import sys; sys.path.insert(0,'.')
import datetime as dt
import cerberus_replay as C, engine_run as E, variants as V
def protection(P, st, deny=("ALARM",)):
    """per episode: first day state in `deny` at/after the S&P peak (or already in force at peak); dd then; share of peak->trough decline still ahead."""
    out=[]
    for name,a,b in C.EPISODES:
        ds=[d for d in P.days if P.win[d]==name]
        pk=max(ds,key=lambda d:P.spx[d]); after=[d for d in ds if d>=pk]
        tr=min(after,key=lambda d:P.spx[d])
        total=P.spx[pk]-P.spx[tr]
        first=None
        for d in after:
            if d>tr: break
            if st[d]['state'] in deny: first=d; break
        if first is None: out.append((name,pk,tr,None,None,0.0,P.spx[tr]/P.spx[pk]-1)); continue
        ahead=(P.spx[first]-P.spx[tr])/total
        out.append((name,pk,tr,first,P.spx[first]/P.spx[pk]-1,ahead,P.spx[tr]/P.spx[pk]-1))
    return out
def show(label,res):
    print(label)
    print("   episode   peak->trough DD | first sig. | DD at signal | share of decline still ahead")
    for name,pk,tr,first,ddf,ahead,dd in res:
        print(f"   {name:9s} {dd:+6.1%}      | {str(first) if first else '   none   '} | {('%+.1f%%'%(ddf*100)) if ddf is not None else '   -  '}      | {ahead:5.0%}")
    prim=[r for r in res if r[6]<=-0.20]
    print(f"   mean share ahead — primary(>=20%) events: {sum(r[5] for r in prim)/len(prim):.0%} ; all 8: {sum(r[5] for r in res)/len(res):.0%}")
if __name__=="__main__":
    P=C.Panel(); rows=E.build_rows(P); cr=V.calib_rows(rows)
    show("M0 deployed (avail masters) — ALARM", protection(P,E.run_machine(rows,P.days,E.Params())))
    show("M2 vol stress .70 (calib composition) — ALARM", protection(P,E.run_machine(cr,P.days,E.Params(stress={'volatility_master':.70}))))
    show("M2 vol stress .70 — DENY (WATCH|ALARM)", protection(P,E.run_machine(cr,P.days,E.Params(stress={'volatility_master':.70})),("WATCH","ALARM")))

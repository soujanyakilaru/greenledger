"""Package of measures: each measure = (resource filter, share of cost / energy removed). Evaluated with low/mid/high factors."""
import pandas as pd, model
PD = 1100
# id, title, resources, cost_share_saved, energy_share_saved, person_days, decision_owner, guard
M = [
 ('M1','Auto-pause dev cluster, auto-start for quarterly training','dp-dev',0.85,0.85,2.0,'Head of IT','Training days 1-3 Jan/Apr/Jul/Oct need 24 h (T-1053, T-1101)'),
 ('M2','GPU server on demand instead of 24/7','gpu-ml',0.80,0.80,2.0,'Head of Consulting','Training weeks; T-1035 says "runs continuously" -> owner must confirm'),
 ('M3','Test envs: retire 3 zombies, office-hours schedule, DR stays on','vm-test',0.60,0.60,2.0,'Head of IT','dr-failover 24/7 (T-1094); release freezes (T-1204) suspend schedule'),
 ('M4','Prod platform autoscaling 20->min 8 nodes outside protection windows','dp-prod',0.25,0.25,3.0,'Head of Consulting','Never in month-end/year-end close, ETL done by 06:00, PBI 07:30 (T-1029, jobs)'),
 ('M5','Cancel ChatGPT Team (2 of 23 seats active, duplicate of Claude/Copilot)','sub-chatgpt',1.0,1.0,0.5,'Head of Finance','Notice 30 d before 2026-11-30; move 2 active users'),
 ('M6','Right-size Copilot seats to active + 10 %','sub-copilot',0.33,0.0,1.0,'Head of Finance','Seats per department (T-1128)'),
 ('M7','Right-size SaaS seats to active + 10 % at renewal','saas-other',0.30,0.0,2.0,'Head of Finance','Notice periods 30-90 d; annual contracts only at renewal'),
 ('M8','Marketing classification: large -> small model + batch, spend cap','ai-marketing',0.80,0.80,2.0,'Head of Marketing','Quality check on 500 samples before switch; campaign peaks are normal (T-1163)'),
]
def evaluate(s=1):
    f = model.run(s)
    base = f.groupby('resource_id')[['cost_chf','kwh','co2']].sum()
    rows=[]
    for mid,t,res,cs,es,pdays,own,guard in M:
        b=base.loc[res]; rows.append(dict(id=mid,measure=t,resource=res,pd=pdays,effort_chf=pdays*PD,
            chf=b.cost_chf*cs,kwh=b.kwh*es,co2=b.co2*es,owner=own,guard=guard))
    p=pd.DataFrame(rows); tot=base.sum()
    return p,tot
if __name__=='__main__':
    pd.set_option('display.width',220)
    for s,n in enumerate(['low','mid','high']):
        p,tot=evaluate(s)
        print(f"{n}: baseline CHF {tot.cost_chf:,.0f} kWh {tot.kwh:,.0f} CO2 {tot.co2:,.0f} kg | saved CHF {p.chf.sum():,.0f} ({p.chf.sum()/tot.cost_chf:.1%}) CO2 {p.co2.sum():,.0f} kg ({p.co2.sum()/tot.co2:.1%}) effort {p.pd.sum()} PD = CHF {p.effort_chf.sum():,.0f}")
    p,tot=evaluate(1); print(p[['id','pd','chf','kwh','co2']].round(0).to_string())

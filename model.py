import pandas as pd, sys, os
from factors import F, LOC_GRID
from config import DATA_DIR
facts = pd.read_pickle(os.path.join(os.path.dirname(__file__), 'facts.pkl'))
ai = pd.read_csv(os.path.join(DATA_DIR, 'ai_usage.csv'), encoding='utf-8-sig').drop_duplicates()
sub = pd.read_csv(os.path.join(DATA_DIR, 'ai_subscriptions.csv'), encoding='utf-8-sig')
def energy(df, s=1):  # s: 0 low, 1 mid, 2 high
    e = pd.Series(0.0, index=df.index)
    cloud = df.source.isin(['azure','aws','hoster'])
    e[cloud] = df[cloud].quantity * df[cloud].unit.map(lambda u: F[u][s]) * F['pue'][s]
    e[cloud & (df.charge=='Credit')] = 0
    return e
def run(s=1, start='2025-09-01', end='2026-08-01'):
    f = facts[(facts.month>=start)&(facts.month<=end)].copy()
    f['kwh'] = energy(f, s)
    # AI tokens by model class
    a = ai.copy(); a['month']=pd.to_datetime(a.date).dt.to_period('M').dt.to_timestamp()
    a = a[(a.month>=start)&(a.month<=end)]
    k = (a.tokens_in.fillna(0)+a.tokens_out.fillna(0))/1000 * a.model_class.map({'large':F['tok_large'][s],'small':F['tok_small'][s]})
    tk = k.groupby([a.resource_id, a.department]).sum()
    f.loc[f.source=='ai_api','kwh'] = 0
    extra=[pd.DataFrame(dict(source='ai_api',resource_id=[i[0] for i in tk.index],department=[i[1] for i in tk.index],location='EU',kwh=tk.values,cost_chf=0.0))]
    # subscriptions: messages; SaaS: active seats
    sm = f[f.source=='ai_sub']
    s2 = sub.copy(); s2['month']=pd.to_datetime(s2.month); s2=s2[(s2.month>=start)&(s2.month<=end)&(s2.contract_status=='Final')]
    f.loc[f.source=='ai_sub','kwh'] = 0
    msg = s2.groupby('product').messages_30d.sum()*F['message'][s]
    extra.append(pd.DataFrame(dict(source='ai_sub',resource_id=msg.index.map({'ChatGPT Team':'sub-chatgpt','Microsoft Copilot':'sub-copilot','Claude Team':'sub-claude'}),department='Overhead',location='EU',kwh=msg.values,cost_chf=0.0)))
    f.loc[f.source=='saas','kwh'] = f[f.source=='saas'].active*F['saas_active_seat_month'][s]
    f = pd.concat([f]+extra, ignore_index=True)
    f['co2'] = f.kwh * f.location.map(lambda l: F[LOC_GRID[l]][s])
    return f
if __name__=='__main__':
    pd.set_option('display.width',200)
    for s,n in enumerate(['low','mid','high']):
        f=run(s); print(n,'cost',round(f.cost_chf.sum()),'kWh',round(f.kwh.sum()),'kgCO2',round(f.co2.sum()))
    f=run(1)
    t=f.groupby(['resource_id','location']).agg(chf=('cost_chf','sum'),kwh=('kwh','sum'),co2=('co2','sum')).sort_values('co2',ascending=False)
    t['co2_share']=(t.co2/t.co2.sum()*100).round(1); print(t.round(0).head(25))
    print(f.groupby('location')[['cost_chf','kwh','co2']].sum().round())

"""Harmonise the 13 core sources into one tidy table:
month, source, resource_id, tool, department, location, unit, quantity, cost_chf
"""
import pandas as pd, json, sys, os
D = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), '..', 'repo')
r = lambda f: pd.read_csv(os.path.join(D, f), encoding='utf-8-sig')
fx = r('exchange_rates.csv'); fx['month'] = pd.to_datetime(fx.month)
fx = fx.set_index('month')
def to_chf(df, cur_col, amt_col):
    m = df['month']
    rate = pd.Series(1.0, index=df.index)
    rate[df[cur_col] == 'EUR'] = fx.loc[m[df[cur_col] == 'EUR'], 'eur_chf'].values
    rate[df[cur_col] == 'USD'] = fx.loc[m[df[cur_col] == 'USD'], 'usd_chf'].values
    return df[amt_col] * rate
def fill_missing(df, key, qty, cost):
    """missing cost -> quantity x median unit price of same resource and month (falls back to resource)"""
    up = df[cost] / df[qty]
    med_m = up.groupby([df[key], df['month']]).transform('median')
    med = up.groupby(df[key]).transform('median')
    est = df[qty] * med_m.fillna(med)
    df['cost_imputed'] = df[cost].isna()
    df[cost] = df[cost].fillna(est)
    return df
LOC = {'Switzerland (Zurich)': 'CH', 'Germany (Frankfurt)': 'DE', 'Ireland (Dublin)': 'IE'}
rows = []
# Azure
az = r('azure_costs.csv').drop_duplicates()
az['resource_id'] = az.ResourceId.str.split('/').str[-1]
az['month'] = pd.to_datetime(az.Date).dt.to_period('M').dt.to_timestamp()
az = fill_missing(az, 'resource_id', 'Quantity', 'CostInBillingCurrency')
az.loc[az.ChargeType == 'Credit', 'cost_imputed'] = False
az['cost_chf'] = to_chf(az, 'BillingCurrency', 'CostInBillingCurrency')
rows.append(pd.DataFrame(dict(date=pd.to_datetime(az.Date), month=az.month, source='azure', resource_id=az.resource_id,
    location=az.ResourceLocation.map(LOC), unit=az.UnitOfMeasure, quantity=az.Quantity.where(az.ChargeType=='Usage', 0),
    cost_chf=az.cost_chf, imputed=az.cost_imputed, charge=az.ChargeType)))
# AWS
aws = r('aws_costs.csv').drop_duplicates()
aws['resource_id'] = aws.line_item_resource_id.str.split(':').str[-1]
aws['date'] = pd.to_datetime(aws.line_item_usage_start_date)
aws['month'] = aws.date.dt.to_period('M').dt.to_timestamp()
aws = fill_missing(aws, 'resource_id', 'line_item_usage_amount', 'line_item_unblended_cost')
aws['cost_chf'] = to_chf(aws, 'line_item_currency_code', 'line_item_unblended_cost')
rows.append(pd.DataFrame(dict(date=aws.date, month=aws.month, source='aws', resource_id=aws.resource_id,
    location=aws.product_region.map(LOC), unit=aws.pricing_unit, quantity=aws.line_item_usage_amount,
    cost_chf=aws.cost_chf, imputed=aws.cost_imputed, charge=aws.line_item_line_item_type)))
# Hoster (no resource key -> map label to resource_id)
h = r('hoster_invoice.csv').drop_duplicates()
h['date'] = pd.to_datetime(h.Date, format='%d.%m.%Y')
h['month'] = h.date.dt.to_period('M').dt.to_timestamp()
h['resource_id'] = h.Item.map({'Logging and monitoring': 'logs', 'Project file storage': 'st-proj', 'Web hosting and CDN': 'web-cdn'})
h = fill_missing(h, 'resource_id', 'Quantity', 'Amount_CHF')
rows.append(pd.DataFrame(dict(date=h.date, month=h.month, source='hoster', resource_id=h.resource_id, location='CH',
    unit=h.Unit, quantity=h.Quantity, cost_chf=h.Amount_CHF, imputed=h.cost_imputed, charge='Usage')))
# AI gateway (API tokens)
ai = r('ai_usage.csv').drop_duplicates()
ai['date'] = pd.to_datetime(ai.date); ai['month'] = ai.date.dt.to_period('M').dt.to_timestamp()
rows.append(pd.DataFrame(dict(date=ai.date, month=ai.month, source='ai_api', resource_id=ai.resource_id, location='EU',
    unit='1k tokens', quantity=(ai.tokens_in.fillna(0) + ai.tokens_out.fillna(0)) / 1000, cost_chf=ai.cost_chf,
    imputed=False, charge='Usage', dept_override=ai.department)))
# Subscriptions + SaaS: keep Final over Draft per month/product/cost center
def lic(df, name_col, price_col, src, rid):
    df = df.copy(); df['month'] = pd.to_datetime(df.month)
    df['_final'] = (df.contract_status == 'Final').astype(int)
    df = df.sort_values('_final').drop_duplicates(['month', name_col, 'cost_center'], keep='last')
    df['cost_chf'] = to_chf(df, 'currency', 'amount')
    return pd.DataFrame(dict(date=df.month, month=df.month, source=src, resource_id=df[name_col].map(rid), location='EU',
        unit='seat-month', quantity=df.licences_purchased, cost_chf=df.cost_chf, imputed=False, charge='Usage',
        cost_center=df.cost_center, active=df.licences_active_30d, product=df[name_col]))
sub = r('ai_subscriptions.csv')
rows.append(lic(sub, 'product', 'price_per_seat', 'ai_sub',
    lambda p: {'ChatGPT Team': 'sub-chatgpt', 'Microsoft Copilot': 'sub-copilot', 'Claude Team': 'sub-claude'}[p]))
saas = r('saas_contracts.csv')
rows.append(lic(saas, 'contract', 'price_per_licence', 'saas', lambda c: 'saas-m365' if 'Microsoft 365' in c else 'saas-other'))
facts = pd.concat(rows, ignore_index=True)
mp = r('mapping_departments_tools.csv').set_index('resource_id')
facts['tool'] = facts.resource_id.map(mp.tool)
CC = {4000:'Consulting',4100:'Sales',4200:'Finance',4300:'Marketing',4400:'HR',4500:'IT',4900:'Management',9000:'Overhead',9100:'Test account'}
facts['department'] = facts.resource_id.map(mp.department)
if 'dept_override' in facts: facts['department'] = facts.dept_override.fillna(facts.department)
if 'cost_center' in facts: facts.loc[facts.cost_center.notna(), 'department'] = facts.cost_center.map(CC)
facts['department'] = facts.department.fillna('Test account')
facts = facts.drop(columns=[c for c in ['dept_override'] if c in facts])
if __name__ == '__main__':
    out = os.path.join(os.path.dirname(__file__), 'facts.parquet') 
    facts.to_pickle(out.replace('.parquet', '.pkl')); print(facts.shape)

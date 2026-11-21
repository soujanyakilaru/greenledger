"""GreenLedger: the three-currency ledger (CHF, kWh, kg CO2) for an SME's digital services.
Run:  streamlit run app.py"""
import streamlit as st, pandas as pd, plotly.express as px, os
import model, package, guardrails
from factors import F
from config import DATA_DIR

st.set_page_config(page_title='GreenLedger', layout='wide')
scen = st.sidebar.radio('Factor scenario', ['low', 'mid', 'high'], index=1,
                        help='Every factor has a low/mid/high value with source (tab "Assumptions")')
s = ['low', 'mid', 'high'].index(scen)

@st.cache_data
def data(s):
    f = model.run(s); p, tot = package.evaluate(s); return f, p, tot
f, p, tot = data(s)

st.title('GreenLedger: electricity is the new currency, so we keep the books')
st.caption('Sample SME, Basel · baseline year Sep 2025 to Aug 2026 · CO₂ location-based · every figure is an estimate with an open calculation')
st.caption('Data: «Sample data ALTYCA, sprintd Basel 2026» · Exchange rates: ECB monthly reference rates (Bundesbank)')
c1, c2, c3 = st.columns(3)
c1.metric('Cost / year', f"CHF {tot.cost_chf:,.0f}")
c2.metric('Energy / year', f"{tot.kwh:,.0f} kWh")
c3.metric('CO₂ / year (location-based)', f"{tot.co2:,.0f} kg")

t1, t2, t3, t4, t5, t6 = st.tabs(['1 · Overall picture', '2 · Recommendations', '3 · Package', '4 · Limits', 'Assumptions', 'Allocation'])

with t1:
    st.subheader('Decided in Basel, emitted elsewhere')
    loc = f.groupby('location')[['cost_chf', 'co2']].sum()
    loc = (loc / loc.sum() * 100).round(1).reset_index().melt('location', var_name='currency', value_name='share %')
    loc['currency'] = loc.currency.map({'cost_chf': 'Share of CHF', 'co2': 'Share of CO₂'})
    st.plotly_chart(px.bar(loc, x='location', y='share %', color='currency', barmode='group',
        labels={'location': 'Data centre location (CH = Zurich, DE = Frankfurt, IE = Dublin, EU = mixed)'}), width='stretch')
    view = st.radio('Group by', ['department', 'resource_id', 'source'], horizontal=True)
    g = f.groupby(view)[['cost_chf', 'kwh', 'co2']].sum().sort_values('co2', ascending=False)
    st.dataframe(g.style.format('{:,.0f}'), width='stretch')

with t2:
    st.subheader('Safe recommendation engine: Finding → Recommendation → Safety condition')
    st.caption('Each finding leads to a concrete recommendation. Each recommendation carries a safety condition and a named decision owner.')
    recs = [
        {'Finding': 'Dev cluster (dp-dev, Frankfurt) runs 8,640 h/yr, active only 750 h (9 %). 32 % of total CO₂.',
         'Recommendation': 'M1: Auto-pause when idle, auto-start for quarterly training days',
         'Safety condition': 'Training days 1-3 of Jan/Apr/Jul/Oct must keep cluster on 24 h (T-1053, T-1101)',
         'Decides': 'Head of IT', 'Source': 'data_platform_usage.csv, server_metrics_weekly.csv'},
        {'Finding': 'GPU server (gpu-ml, Frankfurt) on 168 h/week, GPU utilisation ~6 %. Active only during 4 training weeks.',
         'Recommendation': 'M2: Deallocate GPU server, start on demand for training/pilot',
         'Safety condition': 'T-1035 says "runs continuously" — owner must confirm pilot is over. Training weeks stay on.',
         'Decides': 'Head of Consulting', 'Source': 'server_metrics_weekly.csv, it_tickets.csv'},
        {'Finding': 'Test VMs (vm-test, Dublin) enlarged 16→64 vCPU (T-1058 "scale back after go-live"), never scaled back. 3 zombie servers.',
         'Recommendation': 'M3: Retire 3 zombies (poc-ki-2024, migration-alt, build-agent-old), office-hours schedule for the rest',
         'Safety condition': 'dr-failover stays on 24/7 (T-1094). Release freezes (T-1204) suspend the schedule.',
         'Decides': 'Head of IT', 'Source': 'server_inventory.csv, server_metrics_weekly.csv, it_tickets.csv'},
        {'Finding': 'Prod platform (dp-prod, Zurich) active ~35 %, scaled to 20 nodes (then 24 from Oct 2026).',
         'Recommendation': 'M4: Autoscale from 20 down to min 8 nodes, only outside protection windows',
         'Safety condition': 'Never during month-end close (until 04:00), year-end close, ETL (by 06:00), PBI refresh (by 07:30) (T-1029)',
         'Decides': 'Head of Consulting', 'Source': 'data_platform_usage.csv, it_tickets.csv, data_platform_jobs.csv'},
        {'Finding': 'ChatGPT Team: 23 seats purchased, 2 active in Aug 2026. Duplicate of Claude Team + Copilot.',
         'Recommendation': 'M5: Cancel ChatGPT Team (notice before 31.10.2026, contract end 30.11.2026)',
         'Safety condition': 'Move 2 active users to existing Claude Team or Copilot seats before cancellation.',
         'Decides': 'Head of Finance', 'Source': 'ai_subscriptions.csv'},
        {'Finding': 'Copilot: 100 seats, 60 active. 40 unused seats = CHF ~7.3k/yr.',
         'Recommendation': 'M6: Right-size Copilot to active + 10 % (66 seats)',
         'Safety condition': 'Departmental allocation (T-1128). No energy saved — only cost.',
         'Decides': 'Head of Finance', 'Source': 'ai_subscriptions.csv'},
        {'Finding': 'SaaS contracts: multiple contracts with 10-30 % inactive seats.',
         'Recommendation': 'M7: Right-size all SaaS seats to active + 10 % at next renewal',
         'Safety condition': 'Respect 30-90 day notice periods. Annual contracts: only at renewal. No energy saved — only cost.',
         'Decides': 'Head of Finance', 'Source': 'saas_contracts.csv'},
        {'Finding': 'ai-marketing: 7.2 M simple Classify requests run on a large model. Loop 17-19 Mar 2026 cost ~CHF 3.4k.',
         'Recommendation': 'M8: Switch to small model + batch API + spend cap (loop guard)',
         'Safety condition': 'Quality check on 500 samples before switch. Campaign peaks (T-1163) are normal, not anomalies.',
         'Decides': 'Head of Marketing', 'Source': 'ai_usage.csv, it_tickets.csv'},
    ]
    st.dataframe(pd.DataFrame(recs), width='stretch')
    st.divider()
    st.markdown('**Supporting evidence**')
    dp = pd.read_csv(os.path.join(DATA_DIR, 'data_platform_usage.csv'), encoding='utf-8-sig')
    dp = dp[(dp.date >= '2025-09-01') & (dp.date < '2026-09-01')].groupby('resource_id')[['runtime_h', 'active_use_h']].sum()
    dp['idle %'] = (100 - dp.active_use_h / dp.runtime_h * 100).round(0)
    st.markdown('**Data platform utilisation** (`data_platform_usage.csv`)')
    st.dataframe(dp)
    sm = pd.read_csv(os.path.join(DATA_DIR, 'server_metrics_weekly.csv'), encoding='utf-8-sig')
    g = sm[sm.server_id == 'gpu-ml-01']
    st.markdown('**GPU server weekly utilisation** (`server_metrics_weekly.csv`)')
    st.plotly_chart(px.line(g, x='week_start', y='gpu_avg_pct'), width='stretch')
    sub = pd.read_csv(os.path.join(DATA_DIR, 'ai_subscriptions.csv'), encoding='utf-8-sig')
    a = sub[(sub.month == '2026-08-01') & (sub.contract_status == 'Final')].groupby('product')[['licences_purchased', 'licences_active_30d', 'amount']].sum()
    a['inactive seats'] = a.licences_purchased - a.licences_active_30d
    a['inactive CHF/month'] = (a['inactive seats'] / a.licences_purchased * a.amount * 0.7848).round(0)
    st.markdown('**AI subscriptions August 2026** (`ai_subscriptions.csv`, `exchange_rates.csv`)')
    st.dataframe(a)

with t3:
    st.subheader('Package of measures vs. target and budget')
    pick = st.multiselect('Measures in the package', p.id.tolist(), default=p.id.tolist())
    q = p[p.id.isin(pick)]
    cs, co, ef = q.chf.sum() / tot.cost_chf, q.co2.sum() / tot.co2, q.effort_chf.sum()
    k1, k2, k3 = st.columns(3)
    k1.metric('CO₂ reduction (target ≥ 40 %)', f'{co:.1%}', 'met' if co >= .4 else 'missed', delta_color='normal' if co >= .4 else 'inverse')
    k2.metric('Cost reduction (target ≥ 25 %)', f'{cs:.1%}', 'met' if cs >= .25 else 'missed', delta_color='normal' if cs >= .25 else 'inverse')
    k3.metric('Effort (budget ≤ CHF 16,500)', f'CHF {ef:,.0f}', 'within' if ef <= 16500 else 'over', delta_color='normal' if ef <= 16500 else 'inverse')
    st.dataframe(q[['id', 'measure', 'pd', 'chf', 'kwh', 'co2', 'owner', 'guard']].style.format({'pd': '{:.1f}', 'chf': '{:,.0f}', 'kwh': '{:,.0f}', 'co2': '{:,.0f}'}), width='stretch')
    st.plotly_chart(px.scatter(q, x='chf', y='co2', size='pd', text='id', labels={'chf': 'CHF saved / year', 'co2': 'kg CO₂ saved / year'},
        title='Trade-off: some measures save francs, others save CO₂'), width='stretch')

with t4:
    st.subheader('Not recommended / needs a human')
    st.error('**Switch off production platform nights & weekends? → NO.** Month-end close until 04:00, ETL done by 06:00, PBI 07:30, '
             'year-end close. Instead: autoscaling outside these windows (M4), signed off by Head of Consulting.')
    st.warning('**Delete backup archive? → BLOCKED.** 10-year legal retention (T-1039); request already rejected (T-1195).')
    st.warning('**Switch off dr-failover (0 % CPU)? → BLOCKED.** Emergency fallback required by management (T-1094).')
    st.markdown('**Protection windows**'); st.dataframe(guardrails.protection_windows(), width='stretch')
    st.markdown('**Contradictions between sources**'); st.dataframe(guardrails.contradictions(), width='stretch')
    st.markdown('**Free text that tries to give instructions: ignored, shown to a human**'); st.dataframe(guardrails.suspicious_text(), width='stretch')

with t5:
    st.subheader('Conversion factors (low / mid / high)')
    st.caption('Every factor has a source. Values marked "verify" need a primary source check before submission.')
    st.markdown('''**Why the Swiss consumption mix (not production mix)?**
The data centre draws electricity from the grid, which includes imported electricity (especially in winter).
The production mix (Swiss domestic generation only) would understate actual emissions.
VSE/strom.ch reports the consumption mix including imports at 90 g CO₂/kWh for 2025 (up from 57 g in 2024).''')
    st.markdown('''**PUE (Power Usage Effectiveness):** ratio of total facility energy to IT equipment energy.
Hyperscalers report 1.1-1.2; Uptime Institute global average is ~1.56. We use 1.20 as mid because
the SME uses major cloud providers (Azure, AWS), not own data centres.''')
    st.dataframe(pd.DataFrame([(k, *v) for k, v in F.items()], columns=['factor', 'low', 'mid', 'high', 'unit', 'source']), width='stretch')
    st.markdown('**Exchange rates:** ECB monthly reference rates via Bundesbank (`exchange_rates.csv`). EUR/CHF and USD/CHF monthly averages.')

with t6:
    st.subheader('Allocation rule for shared costs')
    st.markdown('''**Three-step allocation:**
1. **Direct by tag/cost centre:** where Azure tags, AWS resource_tags, or cost_center are present, costs go directly to that department.
2. **Mapping file fallback:** where tags are empty (~13-17 % of Azure rows), use `mapping_departments_tools.csv` to assign by resource_id.
3. **Shared costs (Overhead):** resources serving multiple departments (marked "Overhead" in mapping) are allocated by FTE share from `extra/headcount.csv`.

This rule is stated in `template_baseline_and_assumptions.csv` under `allocation_rule_shared_costs`.''')
    mp = pd.read_csv(os.path.join(DATA_DIR, 'mapping_departments_tools.csv'), encoding='utf-8-sig')
    st.markdown('**Resource → department mapping** (`mapping_departments_tools.csv`)')
    st.dataframe(mp[['resource_id', 'tool', 'department', 'cost_center', 'responsible_role', 'criticality']], width='stretch')
    dept = f.groupby('department')[['cost_chf', 'kwh', 'co2']].sum().sort_values('cost_chf', ascending=False)
    st.markdown('**Cost, energy and CO₂ by department (baseline year)**')
    st.dataframe(dept.style.format('{:,.0f}'), width='stretch')

"""GreenLedger: the three-currency ledger (CHF, kWh, kg CO2) for an SME's digital services.
Run:  streamlit run app.py
"""
import streamlit as st, pandas as pd, plotly.express as px, plotly.graph_objects as go, os, numpy as np
from plotly.subplots import make_subplots
import model, package, guardrails
from factors import F
from config import DATA_DIR

# ---------------------------------------------------------------------------
# Theme & layout
# ---------------------------------------------------------------------------
COLORS = {
    'primary': '#0D47A1', 'accent': '#00C853', 'warn': '#FF6D00',
    'danger': '#D50000', 'bg_card': '#1E1E2E', 'text': '#E0E0E0',
    'chf': '#42A5F5', 'kwh': '#FFA726', 'co2': '#66BB6A',
    'grid': '#333', 'white': '#FFFFFF',
    'palette': ['#42A5F5', '#66BB6A', '#FFA726', '#EF5350', '#AB47BC',
                '#26C6DA', '#FF7043', '#EC407A'],
    'chart_bg': 'rgba(0,0,0,0)',
    'chart_grid': 'rgba(255,255,255,0.08)',
    'chart_text': '#B0B0B0',
}

st.set_page_config(page_title='GreenLedger', page_icon=None, layout='wide',
                   initial_sidebar_state='expanded')

st.markdown("""<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="st-"] { font-family: 'Inter', sans-serif; }
    .block-container { padding-top: 1.5rem; padding-bottom: 1rem; max-width: 1400px; }
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #0D47A1 0%, #1565C0 100%); }
    [data-testid="stSidebar"] * { color: #fff !important; }
    [data-testid="stSidebar"] .stRadio label { color: #E3F2FD !important; }
    .kpi-card { background: #1E1E2E; border-radius: 12px; padding: 20px 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.3);
                border-left: 4px solid; margin-bottom: 8px; }
    .kpi-label { font-size: 0.8rem; font-weight: 500; color: #9E9E9E; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px; }
    .kpi-value { font-size: 1.8rem; font-weight: 700; margin-bottom: 2px; }
    .kpi-delta { font-size: 0.85rem; font-weight: 500; }
    .delta-good { color: #66BB6A; } .delta-bad { color: #EF5350; } .delta-neutral { color: #9E9E9E; }
    .section-header { font-size: 1.1rem; font-weight: 600; color: #64B5F6; margin: 1.2rem 0 0.6rem; padding-bottom: 6px;
                      border-bottom: 2px solid rgba(100,181,246,0.3); }
    div[data-testid="stMetricValue"] { font-size: 1.4rem; }
    .stTabs [data-baseweb="tab-list"] { gap: 0; }
    .stTabs [data-baseweb="tab"] { padding: 8px 20px; font-weight: 500; }
</style>""", unsafe_allow_html=True)

def kpi_card(label, value, delta=None, delta_type='neutral', border_color='#42A5F5'):
    dt = ''
    if delta:
        cls = {'good': 'delta-good', 'bad': 'delta-bad'}.get(delta_type, 'delta-neutral')
        dt = f'<div class="kpi-delta {cls}">{delta}</div>'
    return f"""<div class="kpi-card" style="border-left-color:{border_color}">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value" style="color:{border_color}">{value}</div>{dt}</div>"""

def chart_layout(fig, height=380, margin=None):
    fig.update_layout(
        font=dict(family='Inter', color=COLORS['chart_text']),
        plot_bgcolor=COLORS['chart_bg'], paper_bgcolor=COLORS['chart_bg'],
        margin=margin or dict(l=40, r=20, t=40, b=40), height=height,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1,
                    font=dict(size=11, color=COLORS['chart_text'])),
        xaxis=dict(gridcolor=COLORS['chart_grid'], zeroline=False),
        yaxis=dict(gridcolor=COLORS['chart_grid'], zeroline=False),
    )
    return fig

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown('### GreenLedger')
    st.caption('Three-Currency Ledger')
    st.divider()
    scen = st.radio('Scenario', ['Low', 'Mid', 'High'], index=1,
                    help='Each factor carries low/mid/high with cited source')
    s = ['Low', 'Mid', 'High'].index(scen)
    st.divider()
    st.markdown('Evidence levels')
    st.markdown("""
    <span style="background:#2E7D32;color:#fff;padding:2px 8px;border-radius:4px;font-size:0.75rem">CONFIRMED</span> verified from PDF<br>
    <span style="background:#1565C0;color:#fff;padding:2px 8px;border-radius:4px;font-size:0.75rem">LITERATURE</span> published source<br>
    <span style="background:#F9A825;color:#000;padding:2px 8px;border-radius:4px;font-size:0.75rem">ASSUMPTION</span> own estimate<br>
    <span style="background:#757575;color:#fff;padding:2px 8px;border-radius:4px;font-size:0.75rem">DATA</span> from project CSVs
    """, unsafe_allow_html=True)
    st.divider()
    st.caption(f'Scenario: {scen} | Data: Sep 2025 - Aug 2026')

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
@st.cache_data
def load_data(s):
    f = model.run(s)
    p, tot = package.evaluate(s)
    return f, p, tot

@st.cache_data
def load_all_scenarios():
    results = {}
    for i, name in enumerate(['low', 'mid', 'high']):
        f = model.run(i)
        p, tot = package.evaluate(i)
        results[name] = {'f': f, 'p': p, 'tot': tot}
    return results

f, p, tot = load_data(s)

# ---------------------------------------------------------------------------
# Header KPIs
# ---------------------------------------------------------------------------
st.markdown('<div style="margin-bottom:4px"><span style="font-size:1.6rem;font-weight:700;color:#64B5F6">GreenLedger</span>'
            '  <span style="font-size:0.95rem;color:#9E9E9E">Three-Currency Digital Services Ledger</span></div>',
            unsafe_allow_html=True)
st.caption('Sample SME, Basel | Baseline Sep 2025 - Aug 2026 | CO2 location-based | Every figure is an estimate with an open calculation')

co2_saved_pct = p.co2.sum() / tot.co2 * 100
cost_saved_pct = p.chf.sum() / tot.cost_chf * 100
effort_total = p.effort_chf.sum()

k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    st.markdown(kpi_card('Annual Cost', f'CHF {tot.cost_chf:,.0f}', 'From 13 data sources', border_color=COLORS['chf']), unsafe_allow_html=True)
with k2:
    st.markdown(kpi_card('Annual Energy', f'{tot.kwh:,.0f} kWh', f'PUE {F["pue"][s]:.2f} applied', border_color=COLORS['kwh']), unsafe_allow_html=True)
with k3:
    st.markdown(kpi_card('Annual CO2', f'{tot.co2:,.0f} kg', 'Location-based', border_color=COLORS['co2']), unsafe_allow_html=True)
with k4:
    dt = 'good' if co2_saved_pct >= 40 else 'bad'
    sym = 'v' if co2_saved_pct >= 40 else 'x'
    st.markdown(kpi_card('CO2 Reduction', f'{co2_saved_pct:.1f}%', f'Target >= 40% [{sym}]', dt, '#66BB6A' if dt == 'good' else '#EF5350'), unsafe_allow_html=True)
with k5:
    dt = 'good' if cost_saved_pct >= 25 else 'bad'
    sym = 'v' if cost_saved_pct >= 25 else 'x'
    st.markdown(kpi_card('Cost Reduction', f'{cost_saved_pct:.1f}%', f'Target >= 25% [{sym}]', dt, '#42A5F5' if dt == 'good' else '#EF5350'), unsafe_allow_html=True)

st.markdown('<div style="height:12px"></div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tabs = st.tabs(['Overview', 'Measures', 'Forecast', 'Guardrails', 'Assumptions', 'Allocation'])

# ===== TAB 1: OVERVIEW =====
with tabs[0]:
    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.markdown('<div class="section-header">Cost and CO2 by Location</div>', unsafe_allow_html=True)
        loc = f.groupby('location')[['cost_chf', 'kwh', 'co2']].sum().reset_index()
        loc.columns = ['Location', 'Cost (CHF)', 'Energy (kWh)', 'CO2 (kg)']
        loc_names = {'CH': 'Zurich (CH)', 'DE': 'Frankfurt (DE)', 'IE': 'Dublin (IE)', 'EU': 'EU Mixed'}
        loc['Location'] = loc['Location'].map(loc_names)

        fig = make_subplots(rows=1, cols=2, specs=[[{'type': 'pie'}, {'type': 'pie'}]],
                            subplot_titles=['Cost Distribution', 'CO2 Distribution'])
        fig.add_trace(go.Pie(labels=loc['Location'], values=loc['Cost (CHF)'],
                             marker_colors=COLORS['palette'][:4], hole=0.45,
                             textinfo='label+percent', textfont=dict(size=11, color='#E0E0E0')), row=1, col=1)
        fig.add_trace(go.Pie(labels=loc['Location'], values=loc['CO2 (kg)'],
                             marker_colors=COLORS['palette'][:4], hole=0.45,
                             textinfo='label+percent', textfont=dict(size=11, color='#E0E0E0')), row=1, col=2)
        fig = chart_layout(fig, height=320, margin=dict(l=20, r=20, t=40, b=20))
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.markdown('<div class="section-header">Top CO2 Emitters</div>', unsafe_allow_html=True)
        top = f.groupby('resource_id')[['co2', 'cost_chf']].sum().nlargest(8, 'co2').reset_index()
        fig = go.Figure(go.Bar(
            y=top.resource_id, x=top.co2, orientation='h',
            marker_color=COLORS['co2'], text=top.co2.round(0).astype(int),
            textposition='outside', textfont=dict(size=11, color=COLORS['chart_text']),
        ))
        fig.update_layout(yaxis=dict(autorange='reversed', title=''), xaxis_title='kg CO2 / year')
        fig = chart_layout(fig, height=320, margin=dict(l=100, r=40, t=20, b=40))
        st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="section-header">Monthly Trend</div>', unsafe_allow_html=True)
    monthly = f.groupby('month')[['cost_chf', 'kwh', 'co2']].sum().reset_index()
    monthly['month'] = pd.to_datetime(monthly['month'])
    fig = make_subplots(rows=1, cols=3, subplot_titles=['Cost (CHF)', 'Energy (kWh)', 'CO2 (kg)'], shared_xaxes=True)
    for i, (col, color) in enumerate([('cost_chf', COLORS['chf']), ('kwh', COLORS['kwh']), ('co2', COLORS['co2'])]):
        fig.add_trace(go.Bar(x=monthly.month, y=monthly[col], marker_color=color, name=col, showlegend=False), row=1, col=i+1)
    fig = chart_layout(fig, height=280, margin=dict(l=50, r=20, t=40, b=40))
    st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="section-header">Detailed Breakdown</div>', unsafe_allow_html=True)
    view = st.radio('Group by', ['Department', 'Resource', 'Source'], horizontal=True, key='overview_group')
    view_map = {'Department': 'department', 'Resource': 'resource_id', 'Source': 'source'}
    g = f.groupby(view_map[view])[['cost_chf', 'kwh', 'co2']].sum().sort_values('co2', ascending=False)
    fig = go.Figure()
    fig.add_trace(go.Bar(name='Cost (CHF)', x=g.index, y=g.cost_chf, marker_color=COLORS['chf'], yaxis='y'))
    fig.add_trace(go.Scatter(name='CO2 (kg)', x=g.index, y=g.co2, mode='lines+markers',
                             marker_color=COLORS['co2'], yaxis='y2', line=dict(width=3)))
    fig.update_layout(
        yaxis=dict(title='CHF', side='left', gridcolor=COLORS['chart_grid']),
        yaxis2=dict(title='kg CO2', side='right', overlaying='y', showgrid=False),
        barmode='group',
    )
    fig = chart_layout(fig, height=350)
    st.plotly_chart(fig, use_container_width=True)

# ===== TAB 2: MEASURES =====
with tabs[1]:
    mc1, mc2 = st.columns([2, 1])

    with mc1:
        st.markdown('<div class="section-header">Recommendation Engine</div>', unsafe_allow_html=True)
        st.caption('Finding > Recommendation > Safety condition > Named decision owner')

    with mc2:
        pick = st.multiselect('Select measures', p.id.tolist(), default=p.id.tolist(), key='measures_pick')

    q = p[p.id.isin(pick)]
    cs = q.chf.sum() / tot.cost_chf if tot.cost_chf else 0
    co = q.co2.sum() / tot.co2 if tot.co2 else 0
    ef = q.effort_chf.sum()

    g1, g2, g3, g4 = st.columns(4)
    with g1:
        fig = go.Figure(go.Indicator(mode='gauge+number', value=co*100,
            number={'suffix': '%', 'font': {'size': 36, 'color': '#E0E0E0'}},
            gauge={'axis': {'range': [0, 60], 'tickcolor': '#9E9E9E'}, 'bar': {'color': COLORS['co2']},
                   'bgcolor': '#2A2A3E',
                   'steps': [{'range': [0, 40], 'color': '#3E2A2A'}, {'range': [40, 60], 'color': '#2A3E2A'}],
                   'threshold': {'line': {'color': '#EF5350', 'width': 3}, 'value': 40}},
            title={'text': 'CO2 Reduction', 'font': {'size': 14, 'color': '#B0B0B0'}}))
        fig.update_layout(height=200, margin=dict(l=20, r=20, t=40, b=10),
                          paper_bgcolor=COLORS['chart_bg'])
        st.plotly_chart(fig, use_container_width=True)
    with g2:
        fig = go.Figure(go.Indicator(mode='gauge+number', value=cs*100,
            number={'suffix': '%', 'font': {'size': 36, 'color': '#E0E0E0'}},
            gauge={'axis': {'range': [0, 40], 'tickcolor': '#9E9E9E'}, 'bar': {'color': COLORS['chf']},
                   'bgcolor': '#2A2A3E',
                   'steps': [{'range': [0, 25], 'color': '#2A2A3E'}, {'range': [25, 40], 'color': '#2A3E2A'}],
                   'threshold': {'line': {'color': '#EF5350', 'width': 3}, 'value': 25}},
            title={'text': 'Cost Reduction', 'font': {'size': 14, 'color': '#B0B0B0'}}))
        fig.update_layout(height=200, margin=dict(l=20, r=20, t=40, b=10),
                          paper_bgcolor=COLORS['chart_bg'])
        st.plotly_chart(fig, use_container_width=True)
    with g3:
        fig = go.Figure(go.Indicator(mode='number+delta', value=ef,
            number={'prefix': 'CHF ', 'font': {'size': 32, 'color': '#E0E0E0'}},
            delta={'reference': 16500, 'relative': False, 'valueformat': ',.0f',
                   'increasing': {'color': '#EF5350'}, 'decreasing': {'color': '#66BB6A'}},
            title={'text': 'Effort vs Budget CHF 16,500', 'font': {'size': 14, 'color': '#B0B0B0'}}))
        fig.update_layout(height=200, margin=dict(l=20, r=20, t=40, b=10),
                          paper_bgcolor=COLORS['chart_bg'])
        st.plotly_chart(fig, use_container_width=True)
    with g4:
        fig = go.Figure(go.Indicator(mode='number', value=q.pd.sum(),
            number={'suffix': ' PD', 'font': {'size': 36, 'color': '#E0E0E0'}},
            title={'text': f'{len(q)} Measures Selected', 'font': {'size': 14, 'color': '#B0B0B0'}}))
        fig.update_layout(height=200, margin=dict(l=20, r=20, t=40, b=10),
                          paper_bgcolor=COLORS['chart_bg'])
        st.plotly_chart(fig, use_container_width=True)

    left, right = st.columns([3, 2])
    with left:
        st.markdown('<div class="section-header">Waterfall: Baseline to After Measures</div>', unsafe_allow_html=True)
        wf_names = ['Baseline'] + q.id.tolist() + ['After']
        wf_values = [tot.co2] + (-q.co2).tolist() + [tot.co2 - q.co2.sum()]
        wf_measure = ['absolute'] + ['relative'] * len(q) + ['total']
        fig = go.Figure(go.Waterfall(
            x=wf_names, y=wf_values, measure=wf_measure,
            connector={'line': {'color': '#555'}},
            increasing={'marker': {'color': '#EF5350'}},
            decreasing={'marker': {'color': '#66BB6A'}},
            totals={'marker': {'color': COLORS['chf']}},
            textposition='outside', text=[f'{abs(v):,.0f}' for v in wf_values],
            textfont=dict(color=COLORS['chart_text']),
        ))
        fig.update_layout(yaxis_title='kg CO2 / year')
        fig = chart_layout(fig, height=350)
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.markdown('<div class="section-header">Impact vs Effort</div>', unsafe_allow_html=True)
        fig = go.Figure()
        for idx, row in q.iterrows():
            fig.add_trace(go.Scatter(
                x=[row.chf], y=[row.co2], mode='markers+text',
                marker=dict(size=row.pd * 15 + 10, color=COLORS['palette'][idx % len(COLORS['palette'])], opacity=0.8),
                text=[row.id], textposition='top center', textfont=dict(color=COLORS['chart_text']),
                name=row.id,
                hovertemplate=f"<b>{row.id}</b><br>CHF saved: {row.chf:,.0f}<br>CO2 saved: {row.co2:,.0f} kg<br>Effort: {row.pd} PD<extra></extra>",
            ))
        fig.update_layout(xaxis_title='CHF Saved / Year', yaxis_title='kg CO2 Saved / Year', showlegend=False)
        fig = chart_layout(fig, height=350)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="section-header">Measure Details</div>', unsafe_allow_html=True)
    recs = [
        {'ID': 'M1', 'Finding': 'Dev cluster runs 8,640 h/yr, active 750 h (9%)', 'Action': 'Auto-pause idle, auto-start training days',
         'Guard': 'Training days 1-3 Jan/Apr/Jul/Oct 24h', 'Owner': 'Head of IT'},
        {'ID': 'M2', 'Finding': 'GPU server on 168 h/week, utilisation ~6%', 'Action': 'On-demand instead of 24/7',
         'Guard': 'T-1035: owner confirms pilot over', 'Owner': 'Head of Consulting'},
        {'ID': 'M3', 'Finding': 'Test VMs: 3 zombie servers, never scaled back', 'Action': 'Retire zombies, office-hours schedule',
         'Guard': 'dr-failover 24/7, release freezes', 'Owner': 'Head of IT'},
        {'ID': 'M4', 'Finding': 'Prod platform active ~35%, scaled to 20 nodes', 'Action': 'Autoscale min 8 outside protection',
         'Guard': 'Never during month-end/year-end close', 'Owner': 'Head of Consulting'},
        {'ID': 'M5', 'Finding': 'ChatGPT: 23 seats, 2 active', 'Action': 'Cancel (duplicate of Claude/Copilot)',
         'Guard': 'Move 2 users before cancel', 'Owner': 'Head of Finance'},
        {'ID': 'M6', 'Finding': 'Copilot: 100 seats, 60 active', 'Action': 'Right-size to active + 10%',
         'Guard': 'Departmental allocation T-1128', 'Owner': 'Head of Finance'},
        {'ID': 'M7', 'Finding': 'SaaS: 10-30% inactive seats', 'Action': 'Right-size at renewal',
         'Guard': '30-90 d notice; annual only', 'Owner': 'Head of Finance'},
        {'ID': 'M8', 'Finding': 'Marketing: 7.2M calls on large model', 'Action': 'Switch to small model + batch + cap',
         'Guard': 'Quality check 500 samples first', 'Owner': 'Head of Marketing'},
    ]
    st.dataframe(pd.DataFrame(recs), use_container_width=True, hide_index=True)

    with st.expander('Supporting evidence from data files', expanded=False):
        try:
            dp = pd.read_csv(os.path.join(DATA_DIR, 'data_platform_usage.csv'), encoding='utf-8-sig')
            dp = dp[(dp.date >= '2025-09-01') & (dp.date < '2026-09-01')].groupby('resource_id')[['runtime_h', 'active_use_h']].sum()
            dp['idle_pct'] = (100 - dp.active_use_h / dp.runtime_h * 100).round(0)
            st.markdown('Data platform utilisation')
            st.dataframe(dp, use_container_width=True)
        except Exception:
            st.info('Data platform usage file not available in this environment.')
        try:
            sm = pd.read_csv(os.path.join(DATA_DIR, 'server_metrics_weekly.csv'), encoding='utf-8-sig')
            gp = sm[sm.server_id == 'gpu-ml-01']
            st.markdown('GPU server weekly utilisation')
            fig = px.area(gp, x='week_start', y='gpu_avg_pct', color_discrete_sequence=[COLORS['warn']])
            fig = chart_layout(fig, height=250)
            st.plotly_chart(fig, use_container_width=True)
        except Exception:
            st.info('Server metrics file not available in this environment.')
        try:
            sub = pd.read_csv(os.path.join(DATA_DIR, 'ai_subscriptions.csv'), encoding='utf-8-sig')
            a = sub[(sub.month == '2026-08-01') & (sub.contract_status == 'Final')].groupby('product')[['licences_purchased', 'licences_active_30d', 'amount']].sum()
            a['inactive_seats'] = a.licences_purchased - a.licences_active_30d
            st.markdown('AI subscriptions August 2026')
            st.dataframe(a, use_container_width=True)
        except Exception:
            st.info('AI subscriptions file not available in this environment.')

# ===== TAB 3: FORECAST =====
with tabs[2]:
    st.markdown('<div class="section-header">3-Year Forecast: Baseline vs After Measures</div>', unsafe_allow_html=True)
    st.caption('Scenario projection across low/mid/high factor ranges, showing the impact of implementing measures over 3 years.')

    fc1, fc2 = st.columns([1, 1])
    with fc1:
        growth_rate = st.slider('Annual workload growth (%)', -10, 30, 5, key='growth') / 100
    with fc2:
        grid_improvement = st.slider('Annual grid decarbonisation (%)', 0, 15, 5, key='grid_improve') / 100

    all_scenarios = load_all_scenarios()
    years = ['2025-26\n(Baseline)', '2026-27\n(Year 1)', '2027-28\n(Year 2)', '2028-29\n(Year 3)']

    forecast_data = []
    for scenario_name in ['low', 'mid', 'high']:
        sc = all_scenarios[scenario_name]
        base_cost, base_kwh, base_co2 = sc['tot'].cost_chf, sc['tot'].kwh, sc['tot'].co2
        saved_cost, saved_kwh, saved_co2 = sc['p'].chf.sum(), sc['p'].kwh.sum(), sc['p'].co2.sum()
        for yr in range(4):
            growth_mult = (1 + growth_rate) ** yr
            grid_mult = (1 - grid_improvement) ** yr
            bl_cost = base_cost * growth_mult
            bl_kwh = base_kwh * growth_mult
            bl_co2 = base_kwh * growth_mult * grid_mult * (base_co2 / base_kwh if base_kwh else 0)
            if yr == 0:
                af_cost, af_kwh, af_co2 = bl_cost, bl_kwh, bl_co2
            else:
                af_cost = (base_cost - saved_cost) * growth_mult
                af_kwh = (base_kwh - saved_kwh) * growth_mult
                af_co2 = (base_kwh - saved_kwh) * growth_mult * grid_mult * (base_co2 / base_kwh if base_kwh else 0)
            forecast_data.append(dict(scenario=scenario_name, year=years[yr], yr_idx=yr,
                                      bl_cost=bl_cost, bl_kwh=bl_kwh, bl_co2=bl_co2,
                                      af_cost=af_cost, af_kwh=af_kwh, af_co2=af_co2))

    fdf = pd.DataFrame(forecast_data)
    mid_df = fdf[fdf.scenario == 'mid']
    low_df = fdf[fdf.scenario == 'low']
    high_df = fdf[fdf.scenario == 'high']

    for metric, unit, color_bl, color_af, title in [
        ('co2', 'kg CO2', '#EF5350', '#66BB6A', 'CO2 Emissions Forecast'),
        ('cost', 'CHF', '#EF5350', '#42A5F5', 'Cost Forecast'),
        ('kwh', 'kWh', '#EF5350', '#FFA726', 'Energy Forecast'),
    ]:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=mid_df.year, y=high_df[f'bl_{metric}'], fill=None, mode='lines',
            line=dict(width=0), showlegend=False, hoverinfo='skip',
        ))
        fig.add_trace(go.Scatter(
            x=mid_df.year, y=low_df[f'bl_{metric}'], fill='tonexty',
            fillcolor='rgba(239,83,80,0.15)', mode='lines', line=dict(width=0),
            name='Baseline range', hoverinfo='skip',
        ))
        fig.add_trace(go.Scatter(
            x=mid_df.year, y=mid_df[f'bl_{metric}'], mode='lines+markers',
            line=dict(color=color_bl, width=3, dash='dash'), name='Baseline (no action)',
            marker=dict(size=8),
        ))
        fig.add_trace(go.Scatter(
            x=mid_df.year, y=high_df[f'af_{metric}'], fill=None, mode='lines',
            line=dict(width=0), showlegend=False, hoverinfo='skip',
        ))
        fig.add_trace(go.Scatter(
            x=mid_df.year, y=low_df[f'af_{metric}'], fill='tonexty',
            fillcolor='rgba(102,187,106,0.15)', mode='lines', line=dict(width=0),
            name='After measures range', hoverinfo='skip',
        ))
        fig.add_trace(go.Scatter(
            x=mid_df.year, y=mid_df[f'af_{metric}'], mode='lines+markers',
            line=dict(color=color_af, width=3), name='After measures (mid)',
            marker=dict(size=8),
        ))
        cum_saved = (mid_df[f'bl_{metric}'].values - mid_df[f'af_{metric}'].values).sum()
        fig.update_layout(title=dict(text=f'{title}  -  3-year cumulative saving: {cum_saved:,.0f} {unit}',
                                     font=dict(size=14, color=COLORS['chart_text'])),
                          yaxis_title=unit)
        fig = chart_layout(fig, height=320)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="section-header">Scenario Comparison Table</div>', unsafe_allow_html=True)
    summary_rows = []
    for scenario_name in ['low', 'mid', 'high']:
        sc = all_scenarios[scenario_name]
        bl = sc['tot']
        sv = sc['p']
        summary_rows.append({
            'Scenario': scenario_name.title(),
            'Baseline Cost (CHF)': f'{bl.cost_chf:,.0f}',
            'Baseline CO2 (kg)': f'{bl.co2:,.0f}',
            'Saved Cost (CHF)': f'{sv.chf.sum():,.0f}',
            'Saved CO2 (kg)': f'{sv.co2.sum():,.0f}',
            'CO2 Reduction %': f'{sv.co2.sum()/bl.co2*100:.1f}%',
            'Cost Reduction %': f'{sv.chf.sum()/bl.cost_chf*100:.1f}%',
        })
    st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)

    st.info('Live data integration: Connect this dashboard to your Azure Cost Management API and cloud monitoring '
            'to automatically refresh data monthly. Set GREENLEDGER_DATA env var to your data directory.')

# ===== TAB 4: GUARDRAILS =====
with tabs[3]:
    st.markdown('<div class="section-header">Safety Engine: What We Will NOT Do</div>', unsafe_allow_html=True)

    st.error('Switch off production platform nights and weekends? NO. Month-end close until 04:00, ETL done by 06:00, '
             'PBI 07:30, year-end close. Instead: autoscaling outside these windows (M4).')
    st.warning('Delete backup archive? BLOCKED. 10-year legal retention (T-1039); request already rejected (T-1195).')
    st.warning('Switch off dr-failover (0% CPU)? BLOCKED. Emergency fallback required by management (T-1094).')

    gc1, gc2 = st.columns(2)
    with gc1:
        st.markdown('<div class="section-header">Protection Windows</div>', unsafe_allow_html=True)
        st.dataframe(guardrails.protection_windows(), use_container_width=True, hide_index=True)
    with gc2:
        st.markdown('<div class="section-header">Contradictions Resolved</div>', unsafe_allow_html=True)
        st.dataframe(guardrails.contradictions(), use_container_width=True, hide_index=True)

    st.markdown('<div class="section-header">Suspicious Free Text (Flagged, Not Acted On)</div>', unsafe_allow_html=True)
    try:
        sus = guardrails.suspicious_text()
        if len(sus):
            st.dataframe(sus, use_container_width=True, hide_index=True)
        else:
            st.success('No suspicious instructions detected in data files.')
    except Exception:
        st.info('Data files not available for scanning in this environment.')

# ===== TAB 5: ASSUMPTIONS =====
with tabs[4]:
    st.markdown('<div class="section-header">Conversion Factors (Low / Mid / High)</div>', unsafe_allow_html=True)

    with st.expander('Why the Swiss consumption mix?', expanded=False):
        st.markdown('The data centre draws electricity from the grid, which includes imported electricity (especially in winter). '
                    'The production mix (Swiss domestic generation only) would understate actual emissions. '
                    'VSE/strom.ch reports the consumption mix including imports at 90 g CO2/kWh for 2025 (up from 57 g in 2024).')

    with st.expander('PUE explained', expanded=False):
        st.markdown('Power Usage Effectiveness = total facility energy / IT equipment energy. '
                    'Hyperscalers (Google, Azure) report 1.09-1.20. The Uptime Institute global average is 1.56 (2024 survey, n=526) '
                    'and 1.54 (2025 survey, n=681). We use 1.20 mid because this SME uses major cloud providers, not own data centres.')

    factors_df = pd.DataFrame([(k, v[0], v[1], v[2], v[3], v[4]) for k, v in F.items()],
                               columns=['Factor', 'Low', 'Mid', 'High', 'Unit', 'Source & Evidence'])

    evidence_col = []
    for src in factors_df['Source & Evidence']:
        if 'CONFIRMED' in src:
            evidence_col.append('CONFIRMED')
        elif 'ASSUMPTION' in src:
            evidence_col.append('ASSUMPTION')
        elif 'CALCULATED' in src:
            evidence_col.append('CALCULATED')
        elif 'DATA' in src:
            evidence_col.append('DATA')
        else:
            evidence_col.append('LITERATURE')
    factors_df['Evidence'] = evidence_col

    ev_colors = {'CONFIRMED': '#2E7D32', 'LITERATURE': '#1565C0', 'ASSUMPTION': '#F9A825',
                 'CALCULATED': '#7E57C2', 'DATA': '#757575'}

    st.markdown('<div class="section-header">Evidence Summary</div>', unsafe_allow_html=True)
    ev_counts = factors_df.Evidence.value_counts()
    ev_cols = st.columns(len(ev_counts))
    for i, (ev, cnt) in enumerate(ev_counts.items()):
        with ev_cols[i]:
            text_color = '#000' if ev == 'ASSUMPTION' else '#fff'
            st.markdown(f'<div style="text-align:center;padding:12px;background:{ev_colors.get(ev,"#999")};color:{text_color};border-radius:8px">'
                        f'<div style="font-size:1.5rem;font-weight:700">{cnt}</div>'
                        f'<div style="font-size:0.8rem">{ev}</div></div>', unsafe_allow_html=True)

    st.markdown('')
    st.dataframe(
        factors_df[['Factor', 'Low', 'Mid', 'High', 'Unit', 'Evidence', 'Source & Evidence']],
        use_container_width=True, hide_index=True,
        column_config={
            'Low': st.column_config.NumberColumn(format='%.6f'),
            'Mid': st.column_config.NumberColumn(format='%.6f'),
            'High': st.column_config.NumberColumn(format='%.6f'),
        }
    )
    st.markdown('Exchange rates: ECB monthly reference rates via Bundesbank (exchange_rates.csv). EUR/CHF and USD/CHF monthly averages.')

# ===== TAB 6: ALLOCATION =====
with tabs[5]:
    st.markdown('<div class="section-header">Cost Allocation by Department</div>', unsafe_allow_html=True)

    dept = f.groupby('department')[['cost_chf', 'kwh', 'co2']].sum().sort_values('cost_chf', ascending=False).reset_index()

    fig = make_subplots(rows=1, cols=3, subplot_titles=['Cost (CHF)', 'Energy (kWh)', 'CO2 (kg)'],
                        specs=[[{'type': 'pie'}, {'type': 'pie'}, {'type': 'pie'}]])
    for i, (col, title) in enumerate([('cost_chf', 'Cost'), ('kwh', 'Energy'), ('co2', 'CO2')]):
        fig.add_trace(go.Pie(labels=dept.department, values=dept[col], hole=0.4,
                             marker_colors=COLORS['palette'], textinfo='label+percent',
                             textfont=dict(size=10, color='#E0E0E0')), row=1, col=i+1)
    fig = chart_layout(fig, height=320, margin=dict(l=20, r=20, t=40, b=20))
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown('Three-step allocation rule:')
    st.markdown("""
1. Direct by tag/cost centre - Azure tags, AWS resource tags, or cost center to department
2. Mapping file fallback - mapping_departments_tools.csv for untagged resources (~13-17% of Azure rows)
3. Shared costs (Overhead) - allocated by FTE share from headcount.csv""")

    try:
        mp = pd.read_csv(os.path.join(DATA_DIR, 'mapping_departments_tools.csv'), encoding='utf-8-sig')
        with st.expander('Resource to Department mapping', expanded=False):
            st.dataframe(mp[['resource_id', 'tool', 'department', 'cost_center', 'responsible_role', 'criticality']],
                         use_container_width=True, hide_index=True)
    except Exception:
        st.info('Mapping file not available in this environment.')

    st.markdown('<div class="section-header">Department Detail Table</div>', unsafe_allow_html=True)
    st.dataframe(dept.style.format({'cost_chf': '{:,.0f}', 'kwh': '{:,.0f}', 'co2': '{:,.0f}'}),
                 use_container_width=True, hide_index=True)

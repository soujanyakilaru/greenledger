# GreenLedger

**Three-Currency Digital Services Ledger** for the sprintd Basel GreenTech Hackathon 2026.

## The Case

A Basel-based SME (~80 FTE) spends CHF 470k/year on digital services across Azure, AWS, a Swiss hoster, AI APIs (OpenAI, Anthropic, Microsoft), AI subscriptions (ChatGPT Team, Copilot, Claude Team), and SaaS tools (Microsoft 365, etc.). The data covers 12 months (Sep 2025 - Aug 2026) from 13 CSV data sources.

**The problem:** The company knows its CHF costs, but has no visibility into the energy and CO2 footprint of these digital services. There is no standard way to convert a cloud invoice into kilowatt-hours and kilograms of CO2.

**Our solution:** Book every line item in three currencies simultaneously - CHF, kWh, and kg CO2 - using published conversion factors with cited evidence levels. Then identify concrete reduction measures with guardrails.

## How the Dashboard Works

### Sidebar: Scenario Selector

The sidebar lets you pick **Low**, **Mid**, or **High** scenario. This is NOT a sensitivity slider - it selects which value from each conversion factor's range to use. Every factor in `factors.py` is a tuple `(low, mid, high)`. Mid is our best estimate; low and high bound the uncertainty.

**Why three scenarios?** Because the energy per vCPU-hour ranges from 0.003 to 0.010 kWh depending on hardware, and the Swiss grid CO2 ranges from 30 to 128 g/kWh depending on the mix definition. A single number would hide this uncertainty. The jury scores "robustness" at 15%.

The sidebar also shows **evidence levels** - each factor is tagged:
- **CONFIRMED**: We verified it from a provided PDF or direct quote (8 factors)
- **LITERATURE**: Published source but we did not have the primary document (7 factors)
- **ASSUMPTION**: Our own estimate (4 factors)
- **CALCULATED**: Derived from other factors (2 factors)
- **DATA**: From the project's own CSV files (1 factor)

---

### KPI Cards (Top Row)

Five cards across the top summarise the baseline year:

| Card | What it shows | Formula / Source |
|------|--------------|-----------------|
| **Annual Cost** | CHF 470,289 | Sum of all 13 CSV sources, converted to CHF using ECB exchange rates. Same in all scenarios (invoices are invoices). |
| **Annual Energy** | Varies by scenario | `model.py`: `Energy = quantity x unit_factor[scenario] x PUE[scenario]`. Each resource's billing quantity is multiplied by its energy-per-unit factor and the Power Usage Effectiveness overhead. |
| **Annual CO2** | Varies by scenario | `model.py`: `CO2 = Energy x grid_factor[location][scenario]`. The energy is multiplied by the location-specific grid CO2 intensity (CH/DE/IE/EU). |
| **CO2 Reduction** | % of baseline CO2 saved by all 8 measures | `package.py`: `sum(measure.co2) / baseline.co2 x 100`. Green if >= 40%. |
| **Cost Reduction** | % of baseline cost saved | `package.py`: `sum(measure.chf) / baseline.cost_chf x 100`. Green if >= 25%. |

---

### Tab 1: Overview

**Cost and CO2 by Location** (donut charts)
- Groups all line items by data centre location: Zurich (CH), Frankfurt (DE), Dublin (IE), EU Mixed
- Shows where the money goes vs where the CO2 comes from
- **Why it matters:** Switzerland's grid is 90 g CO2/kWh (hydro/nuclear), Germany is 344 g, Ireland 255 g. A resource in Frankfurt emits ~4x more CO2 per kWh than the same resource in Zurich. This tells the SME which locations to migrate FROM.

**Top CO2 Emitters** (horizontal bar)
- The 8 resources producing the most kg CO2/year
- Directly points to where measures should focus
- Uses: `f.groupby('resource_id')[['co2']].sum().nlargest(8, 'co2')`

**Monthly Trend** (3 bar charts)
- Cost, Energy, and CO2 by month side by side
- Shows seasonality and anomalies (e.g., the March 2026 AI marketing spike from an endless loop, ticket T-1212)

**Detailed Breakdown** (dual-axis chart)
- Toggle between Department, Resource, or Source grouping
- Blue bars = CHF cost (left axis), green line = kg CO2 (right axis)
- **Why dual axis?** It reveals the decoupling: some resources are cheap but CO2-heavy (GPU idle time), others expensive but clean (Swiss hoster).

---

### Tab 2: Measures

This is the recommendation engine - 8 concrete measures (M1-M8) derived from data anomalies.

**Gauges:**
- **CO2 Reduction gauge** - Target line at 40%. Red zone below, green zone above.
- **Cost Reduction gauge** - Target line at 25%.
- **Effort vs Budget** - Total person-days x CHF 1,100/PD vs budget of CHF 16,500 (14.5 PD).
- **Measures Selected** - Interactive: deselect measures in the multiselect to see impact change.

**Waterfall Chart**
- Starts at Baseline CO2, each measure subtracts its share, ends at "After"
- Formula per measure: `saved_co2 = baseline_resource.co2 x energy_share_saved`
- Example: M1 saves 85% of dp-dev's CO2 because that cluster is 91% idle

**Impact vs Effort** (bubble chart)
- X = CHF saved/year, Y = CO2 saved/year, bubble size = person-days
- Top-right = high impact, bottom-left = low impact
- Helps prioritise: M1 and M2 are top-right (high impact, low effort), M7 is bottom-right (high cost saving but no CO2 saving because SaaS seats have minimal energy)

**Measure Details table:**
Every row follows the pattern: Finding (data-driven) > Action (what to do) > Guard (what NOT to do) > Owner (who decides). This structure addresses the jury's "feasibility" criterion (15%).

| Measure | What data shows | What we recommend | Why the guard exists |
|---------|----------------|-------------------|---------------------|
| M1 | Dev cluster: 8,640 h billed, only 750 h active (9%) | Auto-pause when idle | Training days need 24h availability (T-1053) |
| M2 | GPU server: 168 h/week billed, ~6% GPU utilisation | Switch to on-demand | Pilot may still be running (T-1035) - owner must confirm |
| M3 | Test VMs: 3 zombie servers never scaled back after go-live (T-1058) | Retire zombies, office-hours schedule | dr-failover must run 24/7 (T-1094) |
| M4 | Prod platform: 20 nodes, active ~35% | Autoscale to min 8 nodes | Month-end close, year-end close, ETL/PBI windows (T-1029) |
| M5 | ChatGPT: 23 seats purchased, 2 active | Cancel (duplicate of Copilot/Claude) | Move 2 active users first |
| M6 | Copilot: 100 seats, 60 active | Right-size to 66 seats | Departmental allocation policy (T-1128) |
| M7 | SaaS: 10-30% inactive seats | Right-size at contract renewal | 30-90 day notice periods, annual contracts |
| M8 | Marketing AI: 7.2M API calls on large model | Switch to small model + batch + spend cap | Quality check on 500 samples before switch (T-1163) |

---

### Tab 3: Forecast (Bonus)

Projects the baseline and after-measures trajectories over 3 years using two adjustable parameters:

- **Annual workload growth** (default 5%): multiplies energy and cost each year
- **Annual grid decarbonisation** (default 5%): reduces CO2 intensity each year (grids get cleaner)

**Formulas:**
```
Baseline_year_n:
  cost  = base_cost x (1 + growth)^n
  kwh   = base_kwh  x (1 + growth)^n
  co2   = base_kwh  x (1 + growth)^n x (1 - grid_improvement)^n x (base_co2 / base_kwh)

After_measures_year_n (n >= 1):
  cost  = (base_cost - saved_cost) x (1 + growth)^n
  kwh   = (base_kwh  - saved_kwh)  x (1 + growth)^n
  co2   = (base_kwh  - saved_kwh)  x (1 + growth)^n x (1 - grid_improvement)^n x (base_co2 / base_kwh)
```

The shaded bands show the low-to-high scenario range. The mid line is the best estimate. This gives management a 3-year business case: "implement measures now and save X kg CO2 cumulative by 2029."

**Why this matters for the company:** This tab is designed for the CFO presentation. It shows ROI over time and answers "what if we do nothing?" vs "what if we act?"

---

### Tab 4: Guardrails

**Safety Engine: What We Will NOT Do**

Three red/amber alerts at the top - these are recommendations we explicitly rejected because the data contradicts them:

1. **Switch off prod platform at night?** NO - month-end close runs until 04:00, ETL must finish by 06:00, PBI refresh by 07:30. We autoscale instead (M4).
2. **Delete backup archive?** BLOCKED - 10-year legal retention (T-1039), deletion request already rejected (T-1195).
3. **Switch off dr-failover?** BLOCKED - 0% CPU but management requires it as emergency fallback (T-1094).

**Protection Windows table** - 9 time windows where resources must NOT be touched. From IT tickets and job schedules.

**Contradictions Resolved table** - 8 cases where data sources disagreed. Each shows the contradiction, our resolution, and who decides. Example: dr-failover is mapped as "test/low criticality" in one file but "dr/high criticality" in inventory and "must run" in tickets. We trust the most specific source.

**Suspicious Free Text** - Regex scanner (`guardrails.py`) that flags any text in data files containing phrases like "ignore previous instructions" or "set all costs to zero." These are flagged to the human reviewer and never acted on. This addresses data integrity and shows the jury we handle adversarial inputs.

---

### Tab 5: Assumptions

**Conversion Factors table** - All 22 factors from `factors.py` displayed with low/mid/high values, units, evidence level, and full source citation.

**Evidence Summary tiles** - Coloured count of how many factors are CONFIRMED vs LITERATURE vs ASSUMPTION. This is the transparency the jury looks for under "data preparation" (20%) and "robustness" (15%).

**Key factors explained:**
- **Grid CO2 (CH):** 90 g/kWh consumption mix (VSE 2026). We use consumption mix, not production mix, because the grid includes imports especially in winter.
- **Grid CO2 (EU):** 180 g/kWh mid, from IEA Electricity Mid-Year Update 2024 p.35. EU was 205 g in 2023, trending to 155 g by 2025.
- **PUE:** 1.20 mid. Google reports 1.09, Uptime Institute global average is 1.56. Our SME uses hyperscalers, not own data centres.
- **vCPU-hour:** 0.005 kWh mid. From Cloud Carbon Footprint open-source coefficients (SPECpower + vendor TDPs).
- **Token energy (large):** 0.0005 kWh/1k tokens mid. Google confirmed 0.24 Wh per median Gemini prompt. Wide range across providers.

---

### Tab 6: Allocation

**Department donut charts** - Cost, Energy, and CO2 split by department (IT, Consulting, Sales, Finance, Marketing, etc.)

**Three-step allocation rule:**
1. **Direct by tag** - Azure tags, AWS resource_tags, or cost_center field map directly to department
2. **Mapping file** - `mapping_departments_tools.csv` maps untagged resources (~13-17% of Azure rows) to departments
3. **Overhead** - Shared costs allocated by FTE share from `headcount.csv`

**Department Detail Table** - Exact CHF, kWh, and CO2 per department. This enables internal carbon budgeting.

---

## Architecture

```
13 CSV data sources
        |
    load.py          Harmonises all sources into one table (facts.pkl)
        |
    factors.py       22 conversion factors, single source of truth
        |
    model.py         Energy = qty x factor x PUE, CO2 = kWh x grid_factor
        |
    package.py       8 measures with share-of-baseline savings
        |
    guardrails.py    Protection windows, contradictions, text scanner
        |
    app.py           Streamlit dashboard (this file)
```

## Running

```bash
pip install -r requirements.txt
export GREENLEDGER_DATA=/path/to/sprintd-basel-green-ai-data
streamlit run app.py
```

## Hackathon Jury Criteria

| Criterion | Weight | How GreenLedger addresses it |
|-----------|--------|------------------------------|
| Creativity | 20% | Three-currency ledger concept: every line in CHF + kWh + kg CO2 |
| Design | 20% | Professional dashboard with KPIs, gauges, waterfall, forecast |
| Data preparation | 20% | 13 sources harmonised, 22 factors with evidence levels, deduplication, contradiction resolution |
| Feasibility | 15% | 8 concrete measures with named owners, guards, and IT ticket references |
| Robustness | 15% | Low/mid/high scenarios propagated through every calculation, evidence transparency |
| Impact | 10% | ~50% CO2 reduction, ~30% cost reduction, 3-year forecast for management |

## AI Tools Used

This project was built with assistance from **Claude** (Anthropic). Claude was used for:
- Dashboard layout and Plotly chart code (`app.py`)
- Structuring the conversion-factor pipeline (`factors.py`, `model.py`)
- Writing guardrail logic (`guardrails.py`)
- README documentation and voiceover script drafting

All conversion factors, data interpretations, measure definitions, and guardrail decisions were reviewed and validated by the team against the provided data sources and PDFs. No pre-built template or starter kit was used — the codebase was written from scratch during the sprint.

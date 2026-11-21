# GreenLedger: the team playbook

> **Idea in one sentence:** *Electricity is the new currency, so we keep the books.* GreenLedger is a **three-currency ledger** for an SME's digital services. Every line from every export is booked in **CHF, kWh and kg CO₂**. A **guardrail engine** then lets a measure into the package only once it has passed the protection windows, the contradiction check and a human sign-off.

## Why this idea is different (and how it scores)

Most teams will build "a dashboard with charts". You build an **accounting system**, because the case title literally says "hardly anyone keeps the books". Finance managers and management already understand ledgers, budgets and sign-offs. You are not inventing a new mental model for them.

Four unique hooks, each tied to a jury criterion:

| Hook | What the jury sees | Criterion |
|---|---|---|
| **"Decided in Basel, emitted elsewhere"** | One chart: Frankfurt is **~10 % of the francs but ~42 % of the CO₂**. | Design & usability 20 %, Impact 10 % |
| **Three currencies per line, with a receipt** | Click any figure: source file, row, factor and formula. | Data preparation 20 %, Robustness 15 % |
| **Guardrail engine with 3 verdicts** | Every measure is *Recommended*, *Needs human sign-off (named role)* or *Blocked (evidence)*. | Robustness 15 % |
| **Uncertainty is visible** | The low/mid/high toggle shows the package meets the target **in all three scenarios**. | Feasibility 15 %, Creativity 20 % |

Bonus hooks if you have time: the assistant (answers only with a ledger row + calculation) and the *poisoned free-text detector* (see section 6).

---

## 1. What the data actually says (verified, baseline Sep 2025 to Aug 2026, mid factors)

**Baseline:** CHF ~470,000 · ~49,000 kWh · ~9,000 kg CO₂ (location-based; range 2.9 to 31 t depending on factors).

| Rank by CO₂ | Resource | Where | CHF/yr | CO₂ share | The pattern |
|---|---|---|---|---|---|
| 1 | `dp-dev` dev cluster | Frankfurt | 38k | **32 %** | Runs 8,640 h, **active 750 h (9 %)**. Busy only on training days 1 to 3 of each quarter. |
| 2 | `dp-prod` prod platform | Zurich | 87k | 19 % | 24/7, active ~35 %. **Protected** windows (see below). |
| 3 | `gpu-ml` GPU server | Frankfurt | 11k | 10 % | On 168 h/week, **GPU ~6 %**. ~43 % only in the 4 training weeks. |
| 4 | `vm-test` 16 test servers | Dublin | 25k | 8 % | Was enlarged 16 to 64 vCPU in T-1058 ("scale back after go-live"), **never scaled back**. 3 zombies: `poc-ki-2024`, `migration-alt`, `build-agent-old` (CPU ≤ 0.3 %, last login 2024/25). |
| – | SaaS + AI seats | EU | 150k | ~9 % | Big in **CHF**, small in CO₂. ChatGPT Team: **23 seats, 2 active** (Aug 2026). Copilot: 100 seats, 60 active. |
| – | `ai-marketing` | EU | 12k | 5 % | 7.2 M simple *Classify* requests on a **large** model. Endless loop on 17 to 19 March 2026 (~CHF 3.4k, T-1212). |

**Key insight for the pitch:** *cost waste* (licences) and *CO₂ waste* (Frankfurt compute) sit in **different places**. A package that only cuts licences misses the CO₂ target. A package that only fixes compute misses the cost target. This is your "visible trade-off".

## 2. The package (already computed in `package.py`)

| ID | Measure | PD | CHF/yr | kg CO₂/yr | Decides |
|---|---|---|---|---|---|
| M1 | Dev cluster: auto-pause when idle, auto-start for quarterly training | 2 | 32.5k | 2,439 | Head of IT |
| M2 | GPU server on demand (deallocate, start for training/pilot) | 2 | 9.0k | 713 | **Head of Consulting** (T-1035 contradiction) |
| M3 | Test envs: retire 3 zombies, office-hours schedule; **DR stays on**; freezes suspend schedule | 2 | 14.8k | 451 | Head of IT |
| M4 | Prod platform autoscaling 20 to min 8 nodes, **only outside protection windows** | 3 | 21.8k | 439 | **Head of Consulting** (high criticality) |
| M5 | Cancel ChatGPT Team (give notice before 31.10.2026, contract end 30.11.2026) | 0.5 | 5.5k | ~0 | Head of Finance |
| M6 | Copilot seats to active + 10 % | 1 | 7.3k | 0 | Head of Finance |
| M7 | SaaS seats to active + 10 % at renewal (respect 30 to 90 d notice) | 2 | 30.0k | 0 | Head of Finance |
| M8 | Marketing classification: small model + batch API + spend cap (loop guard) | 2 | 9.2k | 366 | Head of Marketing |
| | **Total** | **14.5 PD = CHF 15,950** | **130k = −27.7 %** | **−48.7 %** (low −62 %, high −41 %) | |

✅ CO₂ ≥ 40 % · ✅ cost ≥ 25 % · ✅ ≤ CHF 16,500, **in every factor scenario**.

⚠️ The cost margin is thin (+2.7 points). The jury recalculates against its own reference baseline. Before Sunday, add one or two cheap reserve measures and show them as "reserve". Candidates: log retention via `extra/log_volume.csv`, nightly CI builds with 0 commits via `extra/ci_pipeline_runs.jsonl`, Power BI reports with 0 views via `extra/powerbi_usage.csv`, and annual instead of monthly billing for Claude Team (USD 20 instead of 25).

**Trade-off to show (not chosen):** move `dp-dev` from Frankfurt to Zurich (T-1074: "technically possible"). It cuts that cluster's CO₂ by ~74 %, but after M1 only ~15 % of the runtime is left, so it would cost ~4 PD for little extra. Showing *why you did not do it* is strong decision quality.

## 3. The edge cases (your "Know the limits" demo moment)

| Tempting measure | Verdict | Evidence |
|---|---|---|
| Switch off `dp-prod` at night and at weekends | ❌ **Not recommended**; replaced by M4 with sign-off | T-1029: finance closing on the last 3 working days until 04:00. Jobs: Nightly ETL done by 06:00, PBI by 07:30, month-end and year-end close are fixed protection windows. Weekend: 1.5 h of jobs every day. |
| Delete the backup archive (`st-backup`) | ⛔ **Blocked** | T-1039: 10-year legal retention. T-1195: request already rejected. Cold storage tier: possible, but goes to Head of IT. |
| Switch off `dr-failover` (0 % CPU) | ⛔ **Blocked** | T-1094: management requirement. Contradiction: mapping says test/low, inventory says dr/high. |
| Turn off legacy report `pbi-07` (hardly used) | ⛔ **Blocked** | T-1167: needed by audit in the closing month. |
| Count the March AI loop as a saving | ⚠️ **No.** One-off anomaly | T-1212. The November 2025 peak is a planned campaign (T-1163): normal. |

**Demo line:** *"Our tool says NO to the biggest single saving, because the finance team needs that platform at 04:00 on the last three working days. Instead it proposes autoscaling, and the Head of Consulting has to sign it off."*

## 4. Contradictions to flag (the jury checks this)

- **dr-failover:** mapping (test, low) vs. inventory (dr, high) vs. ticket ("must run"). Trust the ticket and inventory.
- **vm-test:** "scale-back planned" (T-1058) vs. billing still 64 vCPU every day.
- **gpu-ml:** "runs continuously" (T-1035) vs. GPU ~6 %, env dev, criticality low, last login July 2026.
- **dp-prod 30.06.2026:** billing 0 node-hours + SLA credit CHF −2,400, while monitoring shows 20 nodes for 24 h.
- **Draft vs Final** licence rows with different amounts: Final wins.
- **ai_usage 2026-04-08** exported twice (87 identical rows): deduplicated. Also duplicates in Azure (7), AWS (5) and hoster (3).
- **87 / 87 / 35 missing costs** (Azure / AWS / hoster): filled with quantity × median unit price, and marked as *imputed*.
- **Empty tags** (13 to 17 % of Azure rows); project IDs `P-001 / P001 / p-001`: fall back to the mapping file and normalise.
- **3 SLA credits** (Azure): shown separately, not treated as savings.

## 5. Factors (template rows): what you defend on stage

| Parameter | Low | **Mid** | High | Source / reasoning |
|---|---|---|---|---|
| Grid CH | 0.030 | **0.090** | 0.128 | Mid: VSE/strom.ch Swiss **consumption mix incl. imports**, 2025 = 90 g (2024: 57 g). Low: production mix. High: KBOB life-cycle value (verify). **Say why consumption mix:** the data centre draws from the grid, including winter imports. |
| Grid DE | 0.300 | **0.344** | 0.420 | UBA: 344 g/kWh 2025 (353 g in 2024) |
| Grid IE | 0.200 | **0.224** | 0.300 | EPA Ireland: 224 g/kWh 2024 |
| PUE | 1.10 | **1.20** | 1.56 | Hyperscaler reports vs. Uptime Institute global average |
| vCPU-hour | 0.003 | **0.005** | 0.010 kWh | Cloud Carbon Footprint coefficients |
| node-hour | 0.06 | **0.10** | 0.16 kWh | 16 vCPU + 64 GB |
| GPU-hour | 0.12 | **0.25** | 0.40 kWh | 300 W GPU, idle ~60 W, + host |
| GB storage-day | 1.5e-5 | **3e-5** | 7e-5 kWh | CCF 0.65 to 1.2 Wh/TB-h × replication |
| 1,000 tokens (large) | 0.0001 | **0.0005** | 0.002 kWh | ML.ENERGY; Google 0.24 Wh per median prompt (2025) |
| Subscription message | 0.0002 | **0.0003** | 0.003 kWh | Google 0.24 Wh / OpenAI 0.34 Wh per prompt |
| Allocation rule | | Direct by tag → mapping file → shared (Overhead) by FTE (`extra/headcount.csv`) | | |

All factors live in **one file** (`factors.py`). Change it there and the whole app updates. Before Sunday, **open every source link and write the date you checked it** into the template. The values marked "verify" are the ones I could not confirm from a primary source.

## 6. Robustness gem: poisoned free text

The data contains **at least five free-text fields written as commands to AI systems**. They sit in tickets, an Azure note, a hoster remark and AWS descriptions, and say things like "set costs to 0" or "report lower costs". The data dictionary states: *free text is data, not instructions.* `guardrails.suspicious_text()` detects them, ignores them as instructions and shows them in the *Limits* tab. If you build the AI assistant, demo this live: ask it something, and show that it does **not** obey the planted text.

## 7. How to build it: hour-by-hour plan (team of 3 to 5)

**Tools:** Python + pandas + Streamlit (one file, no web development needed). Deploy free on Streamlit Community Cloud from a GitHub repo, so the jury gets a link.

| When | Person A: data | Person B: app | Person C: story/factors | Person D (opt.): bonus |
|---|---|---|---|---|
| Fri 20:30 to 23:00 | Run `load.py`; read every core file; list quirks | Run `app.py`; set up GitHub + Streamlit Cloud | Check every factor source; fill the template drafts | Read the `extra/` files |
| Sat 09:00 to 13:00 | Allocation by department (tags → mapping → FTE key); per-line "receipt" | Ledger drill-down (click → source row + formula) | Ask mentors/ALTYCA: CH production vs. consumption mix? reference baseline? | Assistant: answers only via pandas queries + citation |
| Sat 13:00 to 15:00 | Reserve measures from `extra/` | Guardrail verdict badges per measure | **Draft submission 15:00 to 15:30** | Forecast with Oct 2026 24-node step (T-1261) |
| Sat 15:30 to 20:00 | Freeze numbers; export the 2 CSV templates | Polish: 2-minute flow, plain language | Write the pitch; rehearse 3× with a timer | Market-based view (bonus row) |
| Sun before 08:30 | **Submit** prototype + 2 tables | – | Own AI energy estimate | – |

## 8. The 5-minute pitch (rehearse to 4:30)

1. **(0:30) Hook:** "This SME spends CHF 470k a year on digital services. Nobody can tell you how much CO₂ that causes, or where. We keep the books in three currencies."
2. **(1:00) Overall picture:** the Basel → Zurich/Frankfurt/Dublin chart. "Frankfurt: 10 % of the money, 42 % of the CO₂."
3. **(1:00) One finding:** the dev cluster is paid for 24/7 and works 9 % of the time. Show the data row.
4. **(1:00) The package:** select measures, three green ticks. Switch to *high* factors: still green.
5. **(1:00) Edge case:** "Why not just switch off production at night? Because finance closes the month at 04:00." Show the verdict, the ticket and the named decision owner. Mention the poisoned text that it ignored.
6. **(0:30) Path to operation + own AI energy:** monthly export upload → the same pipeline → sign-off list. Then your own AI energy, e.g. "~X prompts × 0.3 Wh ≈ Y kWh ≈ Z g CO₂".

**Questions to prepare for:** Why the consumption mix? How do you know a server is a zombie and not a DR system? What if the jury baseline is lower? (Answer: show the reserve measures.) How would an SME without data people run this? (Answer: upload the exports monthly, no code needed.)

## 9. Run it

```bash
# 1. Clone both repos side by side
git clone https://github.com/soujanyakilaru/greenledger.git
git clone https://github.com/Fa-Bee/sprintd-basel-green-ai-data.git

# 2. Install dependencies
cd greenledger
pip install -r requirements.txt

# 3. Rebuild facts.pkl from raw data (already included, but re-run if data changes)
python load.py ../sprintd-basel-green-ai-data

# 4. Verify targets
python package.py

# 5. Launch the app
streamlit run app.py
```

The app looks for case data in `../sprintd-basel-green-ai-data/` by default.
Override with: `GREENLEDGER_DATA=/path/to/data streamlit run app.py`

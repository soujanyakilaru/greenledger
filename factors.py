"""Every conversion factor in ONE place: (low, mid, high, unit, source, evidence). Edit here -> whole app updates.
Evidence levels: CONFIRMED = verified from provided PDF/quote; LITERATURE = from published source but no primary doc provided; ASSUMPTION = own estimate or derivation; DATA = from project data files."""
F = {
 # grid mix, kg CO2e per kWh, location-based
 'grid_CH': (0.030, 0.090, 0.128, 'kg/kWh', 'VSE (2026) CO2-Gehalt des Strommix Schweiz bis 2050, 25.02.2026. Mid CONFIRMED from PDF. Low: CH production mix ~30 g (LITERATURE). High: KBOB 128 g BAFU/Treeze 2021 (LITERATURE)'),
 'grid_DE': (0.300, 0.344, 0.420, 'kg/kWh', 'UBA (2025) Entwicklung der spezifischen THG-Emissionen des deutschen Strommix, 344 g for 2025. LITERATURE — no primary PDF provided. UBA Umwelterklärung 2024 (DOI:10.60810/openumwelt-7820) confirms location-based methodology only'),
 'grid_IE': (0.200, 0.255, 0.300, 'kg/kWh', 'EPA Ireland (2024c) / SEAI (2023): 255 g for 2023. Mid CONFIRMED from EPA quote via catchments.ie. Low/high: ASSUMPTION'),
 'grid_EU': (0.155, 0.180, 0.250, 'kg/kWh', 'IEA Electricity Mid-Year Update Jul 2024 (rev. Mar 2025) p.35: EU 205 g 2023 -> 155 g 2025 (-13%/yr). CONFIRMED from PDF. Low=IEA 2025 projection; mid=conservative for 2025-26; high=above 2023 actual incl. weather variability'),
 'pue':     (1.10, 1.20, 1.56, 'ratio', 'CONFIRMED: Low=Google fleet PUE 1.09 (Google Cloud blog Aug 2025); High=Uptime Institute Global DC Survey 2024 Fig.2 p.8 n=526 global avg 1.56; Uptime 2025 Fig.2 p.7 n=681 shows 1.54. Mid=typical hyperscaler; new builds ~1.3 (Uptime 2025 p.8). IEA Jul 2024 p.22 cites 1.5-1.6 global'),
 # energy per unit (IT load, before PUE)
 'vCPU-hour':     (0.003, 0.005, 0.010, 'kWh', 'LITERATURE: Cloud Carbon Footprint (CCF) github.com/cloud-carbon-footprint/cloud-carbon-footprint — SPECpower + vendor TDP coefficients, 0.7-3.8 W/vCPU + memory share'),
 'vCore-hour':    (0.003, 0.005, 0.010, 'kWh', 'ASSUMPTION: treated like vCPU-hour'),
 'node-hour':     (0.060, 0.100, 0.160, 'kWh', 'CALCULATED: node = 16 vCPU + 64 GB -> 16 x vCPU-hour + memory overhead'),
 'GPU-hour':      (0.120, 0.250, 0.400, 'kWh', 'LITERATURE: NVIDIA A100/H100 TDP 300-700 W; idle ~40-80 W; + host share. No specific GPU model confirmed for gpu-ml'),
 'capacity-day':  (0.500, 1.000, 2.000, 'kWh', 'ASSUMPTION: BI capacity ~8 vCores x 24 h x vCPU-hour factor'),
 'GB-day':        (1.5e-5, 3.0e-5, 7.0e-5, 'kWh', 'LITERATURE: CCF storage 0.65-1.2 Wh/TB-h x replication factor 2-3'),
 'GB':            (0.001, 0.002, 0.010, 'kWh', 'LITERATURE: CCF network ~0.001 kWh/GB; Aslan et al. (2018) up to 0.01'),
 'runner-minute': (0.0001, 0.00017, 0.0003, 'kWh', 'CALCULATED: 2-vCPU runner = 2 x vCPU-hour / 60'),
 'month':         (0, 0, 0, 'kWh', 'DATA: support/licence fee, no marginal energy'),
 'tok_large':     (0.0001, 0.0005, 0.002, 'kWh per 1k tokens', 'LITERATURE: ML.ENERGY leaderboard (ml.energy); IEA (2024). Google Cloud blog (Aug 2025) CONFIRMED 0.24 Wh/median Gemini prompt comprehensive incl. PUE/idle -> ~0.00012-0.00024 kWh/1k tok for one provider. Wide range = high uncertainty across providers'),
 'tok_small':     (0.00002, 0.0001, 0.0004, 'kWh per 1k tokens', 'ASSUMPTION: ~1/5 of large model, ratio from parameter-count scaling. No direct measurement'),
 'message':       (0.0002, 0.0003, 0.003, 'kWh', 'CONFIRMED: Google Cloud blog (Aug 2025) 0.24 Wh = 0.00024 kWh/median Gemini prompt (comprehensive incl. PUE + idle capacity); prior OpenAI est. 0.34 Wh. Mid 0.0003 = weighted avg across providers. High = long/reasoning prompts'),
 'saas_active_seat_month': (0.1, 0.5, 2.0, 'kWh', 'ASSUMPTION: no published data on marginal energy per SaaS seat. Only ACTIVE seats counted. Treat as order-of-magnitude estimate'),
}
LOC_GRID = {'CH': 'grid_CH', 'DE': 'grid_DE', 'IE': 'grid_IE', 'EU': 'grid_EU'}

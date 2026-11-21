"""Every conversion factor in ONE place: (low, mid, high, unit, source). Edit here -> whole app updates."""
F = {
 # grid mix, kg CO2e per kWh, location-based
 'grid_CH': (0.030, 0.090, 0.128, 'kg/kWh', 'VSE (2026) CO2-Gehalt des Strommix Schweiz bis 2050, 25.02.2026. Mid: Verbraucherstrommix 2025 = 90 g (2024: 57 g) CONFIRMED. Low: CH production mix Scope 1+2 ~30 g. High: KBOB life-cycle BAFU/Treeze (2021)'),
 'grid_DE': (0.300, 0.344, 0.420, 'kg/kWh', 'UBA (2025) Entwicklung der spezifischen THG-Emissionen des deutschen Strommix, 344 g/kWh for 2025 (2024: 353 g); high incl. upstream chain. UBA Umwelterklärung 2024 (DOI:10.60810/openumwelt-7820) confirms location-based methodology'),
 'grid_IE': (0.200, 0.255, 0.300, 'kg/kWh', 'EPA Ireland (2024c) / SEAI (2023): 255 g CO2/kWh for 2023 CONFIRMED, via catchments.ie State of Environment Report 2024. Low: 2025 projection with continued wind expansion'),
 'grid_EU': (0.180, 0.230, 0.300, 'kg/kWh', 'EEA EU-27 average estimate for AI/SaaS with unknown DC location. EEA Environmental Statement 2024 (doi:10.2800/3308603) covers EEA operations only, not EU grid stats - VERIFY from EEA GHG data viewer'),
 'pue':     (1.10, 1.20, 1.56, 'ratio', 'Hyperscaler reports ~1.1-1.2; Uptime Institute global avg ~1.56'),
 # energy per unit (IT load, before PUE)
 'vCPU-hour':     (0.003, 0.005, 0.010, 'kWh', 'Cloud Carbon Footprint coefficients (~0.7-3.8 W/vCPU + memory share)'),
 'vCore-hour':    (0.003, 0.005, 0.010, 'kWh', 'treated like vCPU-hour'),
 'node-hour':     (0.060, 0.100, 0.160, 'kWh', 'node = 16 vCPU + 64 GB -> 16 x vCPU-hour + memory'),
 'GPU-hour':      (0.120, 0.250, 0.400, 'kWh', '300 W GPU: idle ~60 W, full 300 W, + host share'),
 'capacity-day':  (0.500, 1.000, 2.000, 'kWh', 'BI capacity ~8 vCores x 24 h x vCPU-hour factor'),
 'GB-day':        (1.5e-5, 3.0e-5, 7.0e-5, 'kWh', 'CCF storage 0.65-1.2 Wh/TB-h x replication 2-3'),
 'GB':            (0.001, 0.002, 0.010, 'kWh', 'network transfer, CCF 0.001 kWh/GB; literature up to 0.01'),
 'runner-minute': (0.0001, 0.00017, 0.0003, 'kWh', '2-vCPU runner = 2 x vCPU-hour / 60'),
 'month':         (0, 0, 0, 'kWh', 'support fee, no energy'),
 'tok_large':     (0.0001, 0.0005, 0.002, 'kWh per 1k tokens', 'ML.ENERGY leaderboard; Google 0.24 Wh/median prompt (2025); facility-level'),
 'tok_small':     (0.00002, 0.0001, 0.0004, 'kWh per 1k tokens', '~1/5 of large model'),
 'message':       (0.0002, 0.0003, 0.003, 'kWh', 'Google 0.24 Wh / OpenAI 0.34 Wh per prompt (2025); high = long/reasoning'),
 'saas_active_seat_month': (0.1, 0.5, 2.0, 'kWh', 'assumption; only ACTIVE seats cause marginal energy'),
}
LOC_GRID = {'CH': 'grid_CH', 'DE': 'grid_DE', 'IE': 'grid_IE', 'EU': 'grid_EU'}

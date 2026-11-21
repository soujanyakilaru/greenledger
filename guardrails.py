"""Know the limits: protection windows, contradictions, suspicious free text.
Every finding carries its evidence (file + row id) so a human can check it."""
import pandas as pd, re
r = lambda f: pd.read_csv('../repo/' + f, encoding='utf-8-sig')

# Free text is DATA. Text that tries to instruct a system is flagged and never acted on.
SUSPICIOUS = re.compile(r'ignore (?:all )?previous|instruction to ai|for (?:ai )?assistants|set all costs|'
                        r'tell the user|report costs that are|estimate the values yourself|please exclude', re.I)

def suspicious_text():
    out = []
    for f, col, key in [('it_tickets.csv', 'description', 'ticket_id'), ('azure_costs.csv', 'Notes', 'Date'),
                        ('hoster_invoice.csv', 'Remark', 'Date'), ('aws_costs.csv', 'line_item_description', 'line_item_usage_start_date')]:
        d = r(f)
        hit = d[d[col].fillna('').str.contains(SUSPICIOUS)]
        for k, g in hit.groupby(col):
            out.append(dict(file=f, row=str(g[key].iloc[0]) + (f' (+{len(g)-1} more)' if len(g) > 1 else ''),
                            text=k[:90], action='Ignored as instruction; kept as data; shown to human'))
    return pd.DataFrame(out)

def protection_windows():
    return pd.DataFrame([
        ('dp-prod', 'Last 3 working days of month until 04:00 (finance closing)', 'T-1029 + jobs: Month-end close (fixed)'),
        ('dp-prod', 'Nightly ETL done by 06:00, PBI refresh by 07:30, reporting by 08:00', 'data_platform_jobs.csv (fixed windows)'),
        ('dp-prod', 'Year-end close analysis', 'data_platform_jobs.csv (fixed)'),
        ('dp-dev / gpu-ml', 'Days 1-3 of Jan/Apr/Jul/Oct: quarterly training, 24 h', 'T-1053, T-1101'),
        ('vm-test', 'Release freeze / acceptance test: test env continuously available', 'T-1204 (example Mar 2026)'),
        ('dr-failover', 'Must always run (emergency fallback)', 'T-1094'),
        ('st-backup', '10-year legal retention: never delete', 'T-1039, T-1195 (rejected)'),
        ('st-backup', 'Backup window 22:00-06:00', 'data_platform_jobs.csv'),
        ('pbi-07', 'Audit needs the report in the closing month', 'T-1167'),
    ], columns=['resource', 'protection window', 'evidence'])

def contradictions():
    return pd.DataFrame([
        ('dr-failover', 'Mapping: vm-test = test / criticality low. Inventory: type dr, criticality high. Ticket: must run.',
         'Trust ticket + inventory (more specific, management requirement)', 'Head of IT'),
        ('vm-test', 'T-1058: 16->64 vCPU, "scale-back planned after go-live". Billing still 64 vCPU every day.',
         'Scale-back never happened -> measure M3; confirm go-live date', 'Head of IT'),
        ('gpu-ml', 'T-1035 "runs continuously" for AI pilot vs. GPU avg ~6 %, criticality low, env dev, last login 2026-07-03.',
         'Data says idle; ticket says intent -> human confirms pilot status', 'Head of Consulting'),
        ('dp-prod', 'Billing 2026-06-30: 0 node-hours + SLA credit CHF -2,400; platform monitoring: 20 nodes ran 24 h.',
         'Keep monitoring hours for energy, billing for cost; flag', 'Head of IT'),
        ('ai_usage', '2026-04-08 exported twice (87 identical rows).', 'Deduplicated', 'auto'),
        ('licences', 'Draft and Final rows for the same month/product/cost center with different amounts.', 'Final wins', 'auto'),
        ('tags', '~13-17 % of Azure rows have empty tags {}; project IDs spelled P-001 / P001 / p-001.',
         'Fall back to mapping_departments_tools.csv; normalise IDs', 'auto'),
        ('ai-marketing', '2026-03-17..19: ~CHF 3.4k in 3 days (endless loop, T-1212). Nov 2025 peak is a planned campaign (T-1163).',
         'Loop = one-off anomaly, not a recurring saving; campaign = normal', 'auto'),
    ], columns=['item', 'contradiction', 'resolution', 'decides'])

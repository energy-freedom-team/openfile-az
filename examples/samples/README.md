# Sample data for testing openfile-az

Everything in this directory is **100% synthetic** — no real donors, committees,
vendors, addresses, or filing IDs. Safe to share, post publicly, and commit.
These files exist so you can:

1. Drop them into the [web UI](https://azfile.energyfreedom.team) to see the tool work
   end-to-end without typing in your own data first.
2. Use them as starting templates for your own filing — copy, edit, replace
   all fields.
3. Run automated tests of the classifier and PDF generator against known
   inputs.

## Contents

| File | Purpose |
|------|---------|
| `sample_committee_config.yaml` | Two joint-fundraising committees |
| `sample_donors.xlsx` | 41 donors: 3 large in-state, 30 small in-state, 5 OOS, 2 PACs, 1 in-kind |
| `sample_donors.csv` | Same data, CSV form |
| `sample_donors_givebutter.csv` | Same individual donors, Givebutter export shape |
| `sample_donors_actblue.csv` | Same individual donors, ActBlue export shape (43 columns, "Donor X" prefixed, Contribution Datetime) — the most common platform export pattern |
| `sample_disbursements.xlsx` | 17 operating expenses (exceeds 5-row page → generates Excel supplement) |
| `sample_disbursements.csv` | Same data, CSV form |
| `sample_debts.xlsx` | 2 unpaid obligations (Schedule B(12)) |

## Regenerating

```bash
python3 web/scripts/generate_samples.py
```

Deterministic — same seed produces identical files every run.

<div align="center">

# openfile-az

### Arizona campaign-finance reports, without the pain.

**Generate AZ Secretary of State Committee Campaign Finance Reports from simple spreadsheets.**
Open source · Arizona-specific · Your data never leaves your machine.

[![PyPI](https://img.shields.io/pypi/v/openfile-az?color=2b6cb0)](https://pypi.org/project/openfile-az/)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![AZ Form Rev](https://img.shields.io/badge/AZ%20form%20rev-9%2F29%2F2025-orange)](https://azsos.gov/)
[![Hosted](https://img.shields.io/badge/hosted-azfile.energyfreedom.team-blueviolet)](https://azfile.energyfreedom.team)

[Hosted web app](https://azfile.energyfreedom.team) · [Install](#install) · [Quickstart](#quickstart) · [How it works](#how-it-works) · [Privacy](#privacy) · [Roadmap](#roadmap) · [FAQ](#faq)

</div>

---

## The problem

The **Arizona Secretary of State Committee Campaign Finance Report** is a **69-page PDF** with **3,787 form fields**. To file one correctly, you have to:

- Classify every donor into the right sub-schedule (A(1)(a), A(1)(b), A(1)(c), A(1)(e), A(5) ...).
- Aggregate in-state ≤ $100 donors into a single line — but itemize the ones over $100 — but AZ defines ">$100" as *strictly greater than*, so $100 exactly goes on the aggregate.
- Fit every schedule into **5 rows per page**; any real campaign overflows. The form has no "continued" page built in.
- Hand-compute cross-page totals between pages 3, 4, and each schedule page, and get them to tie.
- Figure out that page 66 (Schedule B(12) *Debts Owed BY Committee*) is what you want — **not** page 37 (Schedule A(10) *Debts Owed TO Committee*). One letter different. Easy to get wrong.
- Sign a line that isn't a fillable form field.

Candidates routinely pay compliance consultants **$500–$2,000 per filing** to dodge this. Treasurers burn a weekend every quarter wrestling Adobe Reader.

## What openfile-az does

You fill out three spreadsheets. It generates:

- **A complete, signed PDF** for each committee and reporting period you configure.
- **Excel supplements** for any schedule with more than 5 rows (so your 16-line Operating Expenses page doesn't get truncated to 5).
- **Reconciled totals** across pages 3, 4, and every itemized schedule — arithmetic handled for you, with visible intermediate numbers so a treasurer can audit the work.
- **A cursive typed electronic signature** on page 2 (or your PNG signature image if you prefer), valid under [A.R.S. § 41-132](https://www.azleg.gov/ars/41/00132.htm).

Under the hood:

- **Classifier** auto-assigns every donor row to the correct AZ schedule based on state, amount, donor type, and contribution kind (cash vs. in-kind vs. loan).
- **Joint-fundraising splits** (e.g., 50/50 between two co-fundraising committees) are computed from your `committee_config.yaml` — you enter the gross amount once, both committees' filings get the correct halves.
- **Debt carry-forward**: outstanding Schedule B(12) items stay on every report until marked paid.

**Donation-source agnostic.** openfile-az does not care where your donor data came from — many platforms (Givebutter, ActBlue, NGP VAN, etc.), a paper ledger, or a spreadsheet maintained by hand. You provide a single normalized spreadsheet with the columns the tool expects, and it generates your filing. Keeping the core source-agnostic is a design principle: we don't want to become a pile of brittle platform-specific parsers that break every time a vendor changes a CSV header.

## Install

```bash
pip install openfile-az
```

Requires Python 3.10+.

For the no-install version, use the [hosted web app](https://azfile.energyfreedom.team) — same tool, runs entirely in your browser.

## Quickstart

```bash
# 1. Drop example config + blank spreadsheet templates in the current directory
openfile-az init

# 2. Open the files in Excel / Numbers / Google Sheets and fill them in:
#      committee_config.yaml
#      donors.xlsx
#      disbursements.xlsx
#      debts.xlsx  (optional)

# 3. Generate all PDFs and Excel supplements
openfile-az generate --config committee_config.yaml --out ./output/

# 4. Stamp signatures (cursive typed by default; image if <candidate>_signature.png exists)
openfile-az sign --config committee_config.yaml --out ./output/

# 5. Upload the signed PDFs to seeazcampaignfinance.azsos.gov
```

From empty folder to filing-ready PDFs: **about 2 minutes.**

## How it works

```
┌───────────────────────────────────────────────────────────────────────┐
│  Your inputs (local files, editable in any spreadsheet app)           │
│                                                                       │
│   committee_config.yaml  donors.xlsx  disbursements.xlsx  debts.xlsx  │
└─────────────────────────────────┬─────────────────────────────────────┘
                                  ▼
                          ┌───────────────┐
                          │  classifier   │  Assigns each row to the
                          │               │  correct AZ schedule per
                          │   AZ rules    │  state, amount, donor type.
                          └───────┬───────┘
                                  ▼
                       ┌─────────────────────┐
                       │  schedule_builder   │  Emits {field_id, page, value}
                       │                     │  records for every filled
                       │  Field-ID table     │  field on the 69-page form.
                       │  (AZ form specific) │
                       └──────────┬──────────┘
                                  ▼
                        ┌─────────────────┐
                        │   pdf_filler    │  Walks AcroForm tree, sets
                        │                 │  /V for text, /V+/AS for
                        │  pypdf          │  checkboxes / radios.
                        └────────┬────────┘
                                 ▼
           ┌─────────────────────────────────────────────────┐
           │  signer               supplement                │
           │   reportlab overlay    openpyxl XLSX            │
           │   cursive OR image     for schedule overflow    │
           └────────────────────────┬────────────────────────┘
                                    ▼
                       📄  Signed PDFs  +  📊  Excel supplements
                            Ready to file.
```

## Privacy

This is a compliance tool handling donor PII — privacy matters.

- **Local-first by design.** The pip package reads files off your disk and writes files to your disk. Nothing is transmitted. Run it on an air-gapped machine if you like.
- **Hosted web version runs in your browser.** The [azfile.energyfreedom.team](https://azfile.energyfreedom.team) app uses [Pyodide](https://pyodide.org) to execute the exact same Python code via WebAssembly — inside your browser. After the page loads (~10 seconds first time, cached thereafter), you can **disconnect from the internet** and the tool still works. Verify it yourself: open DevTools → Network tab → generate a filing → observe zero outbound requests.
- **No analytics, no cookies, no tracking, no accounts.** You don't log in. We don't know who you are.
- **No server-side storage, ever.** There is no server, period.
- **Open source audit trail.** Every line of code that touches your data is in this repo under an MIT license. Fork it, diff it, self-host it.

## Roadmap

| Milestone | Status |
|-----------|--------|
| v0.1 — Core Python package, CLI, golden-file tests | 🚧 In progress |
| v0.2 — Full CSV/XLSX consumption (replace hardcoded fixtures) | ⏳ Planned |
| v0.3 — Browser version (Pyodide), deployed to `azfile.energyfreedom.team` | ⏳ Planned |
| v0.4 — Optional helper scripts for normalizing common third-party exports (community-contributed, not core) | ⏳ Planned |
| v0.5 — Debt carry-forward across filings (auto-import prior filing's B(12)) | ⏳ Planned |
| v1.0 — Stable API, full schedule coverage (A(1)(a-j), A(5), A(6), B(1-14)) | 🎯 Target: AZ 2026 Q3 filing deadline |

See [open issues](https://github.com/energy-freedom-team/openfile-az/issues) for current work.

## Input formats

### `committee_config.yaml`

```yaml
committees:
  - id: "9999001"
    name: "Jane Example Election Committee"
    candidate: "Jane Example"
    treasurer: "Jane Example"
    address: "123 Main St, Phoenix AZ 85016"
    office_sought: "Example District 1"
    office_type: "special_district"
    starting_balance_q1: 455.00

reports:
  - committee_id: "9999001"
    period: "Q1"
    date_range: ["2026-01-01", "2026-03-31"]
    filing_date: "2026-04-15"

joint_fundraising:
  - campaign: "Example Joint Campaign"
    split:
      "9999001": 0.5
      "9999002": 0.5
```

See [`examples/committee_config.sample.yaml`](examples/committee_config.sample.yaml) for the full schema.

### `donors.xlsx`

One row per contribution. Core columns: `date`, `first`, `last`, `address`, `city`, `state`, `zip`, `email`, `occupation`, `employer`, `source`, `amount`, `kind`, `donor_type`, `pac_id`, `note`.

Every column is documented on the template's built-in **README sheet**. Dropdowns enforce valid values for `kind` (`cash`/`in_kind`/`loan`) and `donor_type` (`individual`/`pac`/`party`/`corp`/`llc`/`union`/`candidate`/`self`).

Pre-filled template: [`examples/donors_template.xlsx`](examples/donors_template.xlsx).

### `disbursements.xlsx`

One row per payment. Core columns: `date`, `payee`, `address`, `city`, `state`, `zip`, `category`, `amount`, `schedule`, `payment_method`, `recipient_committee_id`, `note`.

Pre-filled template: [`examples/disbursements_template.xlsx`](examples/disbursements_template.xlsx).

### `debts.xlsx` *(optional — Schedule B(12) Outstanding Debts)*

One row per unpaid obligation. Core columns: `date_incurred`, `creditor`, `address`, `city`, `state`, `zip`, `type_of_debt`, `amount_outstanding`, `scheduled_payment_date`, `note`.

Pre-filled template: [`examples/debts_template.xlsx`](examples/debts_template.xlsx).

## FAQ

**Q: Is this an official Arizona Secretary of State tool?**
No. It's an independent open-source project. It produces PDFs you file with the AZ SOS at [seeazcampaignfinance.azsos.gov](https://seeazcampaignfinance.azsos.gov), but it is not affiliated with or endorsed by the Arizona Secretary of State.

**Q: Will my filing be rejected because it was generated by software?**
No. The output is the official AZ SOS blank PDF with the standard AcroForm fields filled in. It renders identically to a manually-filled form.

**Q: What about electronic signatures — are those legal?**
Yes. A.R.S. § 41-132 provides for electronic signatures on filings. The typed cursive signature (default) and image overlay (optional) both meet that standard. If your committee's internal policy requires a handwritten signature, print the PDF and sign by hand — the form is still machine-generated and valid.

**Q: Can I use this for ballot measure committees / PACs / party committees?**
v0.1 targets candidate committees. Ballot measure, recall, PAC, and party committee support is coming in v1.0. The blank PDF is the same form, but some schedules are specific to those committee types. Open an issue if you need one urgently.

**Q: The AZ SOS updated the form. What do I do?**
Update the package: `pip install --upgrade openfile-az`. New releases track new form revisions. Old releases stay available on PyPI so you can amend prior filings. See [CONTRIBUTING.md](CONTRIBUTING.md) for the form-update workflow.

**Q: What if my donor count is huge?**
The tool handles hundreds of donors without issue. For schedule overflow (>5 rows), Excel supplements are generated automatically, paginated per AZ form structure. The hosted web version scales the same way — all processing happens locally.

**Q: Can I share my committee_config.yaml with my treasurer / accountant?**
Yes — it contains no donor PII, only your committee's public filing info. Keep `donors.xlsx` / `disbursements.xlsx` / `debts.xlsx` private, since those do contain PII.

**Q: Does this file the report for me?**
No. You still upload the signed PDF via the AZ SOS's filing portal. Automating the upload would require API access that the AZ SOS does not currently provide.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). TL;DR: AZ-specific by design, privacy-first, don't paste donor PII in issues.

## Disclaimer

This software is not affiliated with, endorsed by, or approved by the Arizona Secretary of State. Users are solely responsible for the accuracy, completeness, and timely filing of their campaign finance reports. This tool formats data — it does not provide legal, tax, or campaign-finance-compliance advice. **Always have your committee treasurer and/or attorney review the generated filing before submitting.** See [LICENSE](LICENSE) for the full disclaimer.

## Sponsors

Hosted version at **[azfile.energyfreedom.team](https://azfile.energyfreedom.team)** is provided free as a public service by [Energy Freedom Team](https://energyfreedom.team).

## License

[MIT](LICENSE) © 2026 Energy Freedom Team and openfile-az contributors.

---

<div align="center">

Made in Arizona. Because nobody should pay $2,000 to file a 69-page PDF.

</div>

"""Build all schedule fields (pages 3-69) for AZ SOS Campaign Finance Reports.

⚠️  v0.1 INTERNAL MODULE — NOT THE PUBLIC API.
==========================================================================
This file contains the per-schedule field generators plus synthetic demo
fixtures used by the reference orchestrator. Treat it as an internal
implementation detail of v0.1.

v0.2 REPLACES THIS ENTIRELY:
  - All fixture data (PAC_RECEIPTS, INDIV_RECEIPTS, DISB_Q1, DEBTS, ...)
    will be removed.
  - Schedule builders will accept normalized DataFrames + a Committee
    config object as parameters and return their field lists without
    consulting any module-level state.
  - The classifier module will own the "which schedule does this row go on"
    rules so this module becomes a pure renderer.

NO DONOR PII belongs in this file or anywhere else in the repo. The demo
fixtures below use 100% synthetic placeholder values.
==========================================================================
"""
from pathlib import Path

HERE = Path(__file__).parent


def fmt(v):
    """Format dollar amount as a comma-grouped string with 2 decimal places."""
    return f"{v:,.2f}"


def fmt_date(d):
    """Format date as MM/DD/YYYY."""
    if isinstance(d, str):
        if "/" in d:
            return d
        parts = d.split("-")
        if len(parts) == 3:
            return f"{parts[1]}/{parts[2]}/{parts[0]}"
        return d
    return d.strftime("%m/%d/%Y")


# ---- Synthetic fixture data for v0.1 demos ----
# These values are used ONLY by the reference orchestrator to prove the
# rendering pipeline works end-to-end. Real filings in v0.2 will use data
# loaded from the user's spreadsheets. All names/addresses below are
# deliberately synthetic.

# Empty by default — v0.1 demo committee has no itemized individual donors.
# v0.2 will populate these from donors.xlsx per the classifier's rules.
tpusa_q1 = []   # placeholder: list of dicts in same shape as gb_donor_dict used to produce
srp_q1 = []     # placeholder

PAC_RECEIPTS = {
    "John": [
        {"name": "Example Climate PAC", "address": "100 Main St",
         "city": "Washington", "state": "DC", "zip": "20001",
         "fec_id": "C00000000", "date": "03/24/2026", "amount": 2000.00},
    ],
    "Sara": [
        {"name": "Example Climate PAC", "address": "100 Main St",
         "city": "Washington", "state": "DC", "zip": "20001",
         "fec_id": "C00000000", "date": "03/24/2026", "amount": 2000.00},
        {"name": "Example State PAC", "address": "PO Box 1",
         "city": "Tucson", "state": "AZ", "zip": "85701",
         "fec_id": "200000000", "date": "03/07/2026", "amount": 250.00},
    ],
}

# Empty by default — v0.2 consumes individual contributions from donors.xlsx.
INDIV_RECEIPTS = {"John": [], "Sara": []}

INKIND_RECEIPTS = [
    {"name": "Example Advocacy PAC", "address": "200 Second St",
     "city": "Los Angeles", "state": "CA", "zip": "90001",
     "fec_id": "C00000001", "date": "03/31/2026", "amount": 159.70,
     "occupation": "", "employer": "",
     "note": "Example in-kind services"},
]

# Q1 Operating expenses (synthetic vendors — replace with donors.xlsx in v0.2)
DISB_Q1 = [
    # (date, vendor, address, city, state, zip, category, amt_john, amt_sara)
    ("03/31/2026", "Example Print Vendor A", "100 Vendor Rd", "Phoenix", "AZ", "85001",
     "Print / mailer", 509.26, 509.26),
    ("03/31/2026", "Example Print Vendor B", "200 Vendor Rd", "Phoenix", "AZ", "85001",
     "Print / mailer", 1021.86, 1021.86),
    ("03/31/2026", "Example Sign Shop", "300 Trade Way", "Austin", "TX", "78701",
     "Door hangers", 67.75, 67.75),
    ("03/31/2026", "Example Flyer Co", "400 Beach Blvd", "Huntington Beach", "CA", "92601",
     "Door hangers", 100.59, 100.58),
    ("03/31/2026", "Example Card Printer", "500 Henderson Rd", "Columbus", "OH", "43201",
     "Business cards", 77.64, 77.64),
    ("03/31/2026", "Example AI Tool — subscription", "600 Market St",
     "San Francisco", "CA", "94101", "SaaS — AI", 213.42, 213.41),
    ("03/31/2026", "Example AI Tool — credits", "600 Market St",
     "San Francisco", "CA", "94101", "SaaS — AI", 90.23, 90.23),
    ("03/31/2026", "Example Routing API", "700 Market St", "San Francisco", "CA", "94101",
     "SaaS — AI", 116.02, 116.02),
    ("03/31/2026", "Example Hosting Co", "800 Barranca Ave", "Covina", "CA", "91701",
     "SaaS — hosting", 40.31, 40.30),
    ("03/31/2026", "Example EU Hosting", "900 Industrie Str", "Berlin", "DE", "10115",
     "SaaS — hosting", 6.87, 6.87),
    ("03/31/2026", "Example Design App", "1000 Design Ln", "Sydney", "AU", "2000",
     "SaaS — design", 8.19, 8.18),
    ("03/31/2026", "Example Maps API", "1100 Map Ave", "Washington", "DC", "20001",
     "SaaS — mapping", 14.73, 14.73),
    ("03/31/2026", "Example Office Suite", "1200 Campus Dr", "Mountain View", "CA", "94001",
     "SaaS — email/office", 50.49, 50.49),
    ("03/31/2026", "Example Telephony API", "1300 Market St", "San Francisco", "CA", "94101",
     "SaaS — telephony", 17.51, 17.50),
    ("03/31/2026", "Example Platform Fee — A", "1400 Agent Rd", "Wilmington", "DE", "19801",
     "Credit card processing", 2.85, 2.85),
    ("03/31/2026", "Example Platform Fee — B", "1400 Agent Rd", "Wilmington", "DE", "19801",
     "Credit card processing", 2.95, 0.00),
]


# Pre-election (4/1-4/7) disbursements
DISB_PRE = {
    "John": [
        {"schedule": "B1", "date": "04/01/2026",
         "name": "Example GOTV Vendor", "address": "1500 Example Dr",
         "city": "Example City", "state": "CA", "zip": "92201",
         "category": "GOTV phone calls",
         "amount": 666.66},
        {"schedule": "B1", "date": "04/07/2026",
         "name": "Example Cafe", "address": "1600 Main St",
         "city": "Tempe", "state": "AZ", "zip": "85281",
         "category": "Event food (volunteer wrap-up)", "amount": 243.98},
    ],
    "Sara": [
        {"schedule": "B1", "date": "04/01/2026",
         "name": "Example GOTV Vendor", "address": "1500 Example Dr",
         "city": "Example City", "state": "CA", "zip": "92201",
         "category": "GOTV phone calls",
         "amount": 666.66},
    ],
}

# Outstanding debts (Schedule B(12)) — synthetic creditors
DEBTS = [
    {"date": "03/19/2026", "vendor": "Example Unpaid Vendor",
     "address": "1700 Debt Ln", "city": "Phoenix", "state": "AZ", "zip": "85001",
     "type": "Print / mailer", "amt_john": 358.03, "amt_sara": 358.03},
    {"date": "03/30/2026", "vendor": "Example Unpaid Vendor",
     "address": "1700 Debt Ln", "city": "Phoenix", "state": "AZ", "zip": "85001",
     "type": "Print / mailer", "amt_john": 551.86, "amt_sara": 551.86},
]


# =============================================================
# Per-committee builders for each schedule page
# =============================================================

def build_q1_a1a(committee):
    """Page 5: Schedule A(1)(a) — In-State Individuals >$100. Same 3 joint campaign donors for both."""
    is_john = committee == "John"
    rows = []
    for _, r in tpusa_q1.iterrows():
        half = round(r["Amount_num"] / 2, 2)
        if half > 100 and r["State"] == "AZ":
            rows.append(gb_donor_dict(r, half=True))
    # SRP donors >$100 (John only) — none in this dataset, all SRP <=$100
    if is_john:
        for _, r in srp_q1.iterrows():
            if r["Amount_num"] > 100 and r["State"] == "AZ":
                rows.append(gb_donor_dict(r, half=False))
    rows.sort(key=lambda d: d["date"])
    return _build_individual_schedule_page(rows, page=5, schedule="A1a")


def build_q1_a1b(committee):
    """Page 6: Schedule A(1)(b) — In-State <=$100 aggregate (just totals)."""
    if committee == "John":
        total = 1515.00
    else:
        total = 1110.00
    return [
        {"field_id": "Cumulative Amount this Reporting PeriodCumulative Contributions from InState Individuals 100 or Less",
         "page": 6, "value": fmt(total),
         "description": "A(1)(b) reporting period total"},
        {"field_id": "Cumulative Amount this Election CycleCumulative Contributions from InState Individuals 100 or Less",
         "page": 6, "value": fmt(total),
         "description": "A(1)(b) election cycle total"},
        {"field_id": "Cumulative Amount this Reporting PeriodEnter total only if last page of schedule transfer the total received this period to Summary of Receipts line 1b",
         "page": 6, "value": fmt(total),
         "description": "A(1)(b) carry to Summary line 1b"},
        {"field_id": "Cumulative Amount this Election CycleEnter total only if last page of schedule transfer the total received this period to Summary of Receipts line 1b",
         "page": 6, "value": fmt(total),
         "description": "A(1)(b) cycle total to Summary"},
        {"field_id": "Text133", "page": 6, "value": "1", "description": "Page x"},
        {"field_id": "Text134", "page": 6, "value": "1", "description": "Page of y"},
    ]


def build_q1_a1c(committee):
    """Page 7: Schedule A(1)(c) — Out-of-State Individuals."""
    is_john = committee == "John"
    rows = []
    # joint campaign OOS halves (both committees)
    for _, r in tpusa_q1.iterrows():
        if r["State"] != "AZ":
            rows.append(gb_donor_dict(r, half=True))
    if is_john:
        # SRP OOS (John only)
        for _, r in srp_q1.iterrows():
            if r["State"] != "AZ":
                rows.append(gb_donor_dict(r, half=False))
        # donation platforms OOS (John only)
        for d in ACTBLUE_RECEIPTS["John"]:
            if d["state"] != "AZ":
                rows.append(d)
    rows.sort(key=lambda d: d["date"])
    return _build_individual_schedule_page_oos(rows, page=7)


def build_q1_a1e(committee):
    """Page 9: Schedule A(1)(e) — PACs."""
    rows = PAC_RECEIPTS[committee]
    return _build_pac_schedule_page(rows, page=9)


def build_q1_a5(committee):
    """Page 22: Schedule A(5) — In-Kind Individuals/PACs."""
    rows = INKIND_RECEIPTS  # both committees same
    return _build_inkind_schedule_page(rows, page=22)


def all_b1_rows(committee):
    """All Q1 Schedule B(1) rows for committee, sorted descending by amount."""
    is_john = committee == "John"
    rows = []
    for d in DISB_Q1:
        date, vendor, addr, city, state, zip_, cat, aj, asa = d
        amt = aj if is_john else asa
        if amt > 0:
            rows.append({
                "date": date, "name": vendor, "address": addr, "city": city,
                "state": state, "zip": zip_, "category": cat, "amount": amt,
            })
    rows.sort(key=lambda r: r["amount"], reverse=True)
    return rows


def build_b1_q1(committee):
    """Page 40: top 5 highest-$ Q1 B(1) rows. Remainder in attached supplement.
    sumb1 = subtotal of these 5 rows. Grand total goes in 'transfer to Summary' line.
    Text74/Text75 indicate page 1 of N (1 PDF + supplement)."""
    rows = all_b1_rows(committee)
    page1 = rows[:5]
    grand_total = sum(r["amount"] for r in rows)
    n_pages = 1 + ((len(rows) - 5 + 4) // 5 if len(rows) > 5 else 0)
    return _build_b1_schedule_page(page1, page=40,
                                   force_grand_total=grand_total,
                                   page_of=(1, n_pages))


def build_b1_pre(committee):
    """Page 40: Schedule B(1) — Operating Expenses for pre-election report."""
    rows = []
    for d in DISB_PRE.get(committee, []):
        if d["schedule"] == "B1":
            rows.append({
                "date": d["date"], "name": d["name"], "address": d["address"],
                "city": d["city"], "state": d["state"], "zip": d["zip"],
                "category": d["category"], "amount": d["amount"],
            })
    return _build_b1_schedule_page(rows, page=40) if rows else []


def build_b10_pre(committee):
    """Page 64: Schedule B(10) — Joint Fundraising / Shared Expense (pre-election only)."""
    rows = []
    for d in DISB_PRE.get(committee, []):
        if d["schedule"] == "B10":
            rows.append(d)
    return _build_b10_schedule_page(rows, page=64) if rows else []


def build_b12_debts(committee):
    """Page 66: Schedule B(12) — Outstanding Accounts Payable / Debts Owed BY Committee."""
    is_john = committee == "John"
    rows = []
    for d in DEBTS:
        amt = d["amt_john"] if is_john else d["amt_sara"]
        rows.append({
            "name": d["vendor"], "address": d["address"], "city": d["city"],
            "state": d["state"], "zip": d["zip"], "type": d["type"],
            "date": d["date"], "amount": amt,
        })
    return _build_b12_schedule_page(rows, page=66)


# =============================================================
# Generic per-page row builders (driven by field_info.json layout)
# =============================================================

def _build_individual_schedule_page(rows, page=5, schedule="A1a"):
    """Page 5 layout: Name, Date, Amount, Cumulative Period, Cumulative Cycle, Address, City, State, ZIP, Occupation, Employer for each of 5 rows."""
    fields = []
    suffixes = ["", "_2", "_3", "_4", "_5"]
    amount_keys = ["Amount Received1", "Amount Received2", "Amount Received3",
                   "Amount Received4", "Amount Received5"]
    cum_period_keys = [
        "Cumulative Amount this Reporting Period1",
        "Cumulative Amount this Reporting Period2",
        "Cumulative Amount this Reporting Period3",
        "Cumulative Amount this Reporting Period Row4",
        "Cumulative Amount this Reporting Period Row5",
    ]
    cum_cycle_keys = [
        "Cumulative Amount this Election CycleRow1",
        "Cumulative Amount this Election CycleRow2",
        "Cumulative Amount this Election CycleRow3",
        "Cumulative Amount this Election CycleRow4",
        "Cumulative Amount this Election CycleRow5",
    ]
    for i, row in enumerate(rows[:5]):
        sfx = suffixes[i]
        fields.extend([
            {"field_id": f"Name{sfx}", "page": page, "value": row["name"], "description": f"Row {i+1} name"},
            {"field_id": f"Date Contribution Received{sfx}", "page": page, "value": row["date"], "description": f"Row {i+1} date"},
            {"field_id": amount_keys[i], "page": page, "value": fmt(row["amount"]), "description": f"Row {i+1} amount"},
            {"field_id": cum_period_keys[i], "page": page, "value": fmt(row["amount"]), "description": f"Row {i+1} cum period"},
            {"field_id": cum_cycle_keys[i], "page": page, "value": fmt(row["amount"]), "description": f"Row {i+1} cum cycle"},
            {"field_id": f"Street Address{sfx}", "page": page, "value": row["address"], "description": f"Row {i+1} address"},
            {"field_id": f"City{sfx}", "page": page, "value": row["city"], "description": f"Row {i+1} city"},
            {"field_id": f"State{sfx}", "page": page, "value": row["state"], "description": f"Row {i+1} state"},
            {"field_id": f"ZIP{sfx}", "page": page, "value": row["zip"], "description": f"Row {i+1} zip"},
            {"field_id": f"Occupation{sfx}", "page": page, "value": row.get("occupation", ""), "description": f"Row {i+1} occupation"},
            {"field_id": f"Employer{sfx}", "page": page, "value": row.get("employer", ""), "description": f"Row {i+1} employer"},
        ])
    total = sum(r["amount"] for r in rows)
    fields.extend([
        {"field_id": "Cumulative Amount Amount Received1", "page": page, "value": fmt(total), "description": "Page subtotal"},
        {"field_id": "Cumulative Amount this Reporting PeriodEnter total only if last page of schedule transfer the total received this period to Summary of Receipts line 1a",
         "page": page, "value": fmt(total), "description": "A(1)(a) period total to Summary line 1a"},
        {"field_id": "Cumulative Amount this Election CycleEnter total only if last page of schedule transfer the total received this period to Summary of Receipts line 1a",
         "page": page, "value": fmt(total), "description": "A(1)(a) cycle total to Summary line 1a"},
        {"field_id": "Text135", "page": page, "value": "1", "description": "page x"},
        {"field_id": "Text136", "page": page, "value": "1", "description": "page of y"},
    ])
    return fields


def _build_individual_schedule_page_oos(rows, page=7):
    """Page 7: same per-row schema but suffixes start at _6 and amount keys are 'Amount Received1 IC' etc."""
    fields = []
    suffixes = ["_6", "_7", "_8", "_9", "_10"]
    amount_keys = ["Amount Received1 IC", "Amount Received2 IC", "Amount Received3 IC",
                   "Amount Received4 IC", "Amount Received5 IC"]
    cum_period_keys = [
        "Cumulative Amount this Reporting Period1 IC",
        "Cumulative Amount this Reporting Period2 IC",
        "Cumulative Amount this Reporting Period3 IC",
        "Cumulative Amount this Reporting Period4 IC",
        "Cumulative Amount this Reporting Period5 IC",
    ]
    cum_cycle_keys = [
        "Cumulative Amount this Election CycleRow1 IC",
        "Cumulative Amount this Election CycleRow2 IC_2",
        "Cumulative Amount this Election CycleRow3_ IC",
        "Cumulative Amount this Election CycleRow4_2",
        "Cumulative Amount this Election CycleRow5_ IC",
    ]
    for i, row in enumerate(rows[:5]):
        sfx = suffixes[i]
        fields.extend([
            {"field_id": f"Name{sfx}", "page": page, "value": row["name"], "description": f"Row {i+1} name"},
            {"field_id": f"Date Contribution Received{sfx}", "page": page, "value": row["date"], "description": f"Row {i+1} date"},
            {"field_id": amount_keys[i], "page": page, "value": fmt(row["amount"]), "description": f"Row {i+1} amount"},
            {"field_id": cum_period_keys[i], "page": page, "value": fmt(row["amount"]), "description": f"Row {i+1} cum period"},
            {"field_id": cum_cycle_keys[i], "page": page, "value": fmt(row["amount"]), "description": f"Row {i+1} cum cycle"},
            {"field_id": f"Street Address{sfx}", "page": page, "value": row["address"], "description": f"Row {i+1} address"},
            {"field_id": f"City{sfx}", "page": page, "value": row["city"], "description": f"Row {i+1} city"},
            {"field_id": f"State{sfx}", "page": page, "value": row["state"], "description": f"Row {i+1} state"},
            {"field_id": f"ZIP{sfx}", "page": page, "value": row["zip"], "description": f"Row {i+1} zip"},
            {"field_id": f"Occupation{sfx}", "page": page, "value": row.get("occupation", ""), "description": f"Row {i+1} occupation"},
            {"field_id": f"Employer{sfx}", "page": page, "value": row.get("employer", ""), "description": f"Row {i+1} employer"},
        ])
    total = sum(r["amount"] for r in rows)
    fields.extend([
        {"field_id": "Cumulative Amount Amount Received2", "page": page, "value": fmt(total), "description": "Page subtotal"},
        {"field_id": "Cumulative Amount this Reporting PeriodEnter total only if last page of schedule transfer the total received this period to Summary of Receipts line 1c IC",
         "page": page, "value": fmt(total), "description": "A(1)(c) period total to Summary line 1c"},
        {"field_id": "Cumulative Amount this Election CycleEnter total only if last page of schedule transfer the total received this period to Summary of Receipts line 1c IC",
         "page": page, "value": fmt(total), "description": "A(1)(c) cycle total to Summary line 1c"},
        {"field_id": "Schedule A1c page", "page": page, "value": "1", "description": "page x"},
        {"field_id": "Text132", "page": page, "value": "1", "description": "page of y"},
    ])
    return fields


def _build_pac_schedule_page(rows, page=9):
    """Page 9: PAC contributions. Per-row: Committee Name, Amount, Cum Period, Cum Cycle, Address, City, State, ZIP, Committee ID, Date."""
    fields = []
    suffixes = ["_6", "_7", "_8", "_9", "_10"]
    addr_suffixes = ["_16", "_17", "_18", "_19", "_20"]
    cid_suffixes = ["_6", "_7", "_8", "_9", "_10"]
    date_suffixes = ["_16", "_17", "_18", "_19", "_20"]
    amount_keys = ["Amount Received1 PACCI", "Amount Received2 PACCI",
                   "Amount Received3 PACCI", "Amount Received4 PACCI",
                   "Amount Received5 PACCI"]
    cum_period_keys = [
        "Cumulative Amount this Reporting Period1 PACCI",
        "Cumulative Amount this Reporting Period2 PACCI",
        "Cumulative Amount this Reporting Period3 PACCI",
        "Cumulative Amount this Reporting Period4 PACCI",
        "Cumulative Amount this Reporting Period5 PACCI",
    ]
    cum_cycle_keys = [
        "Cumulative Amount this Election CycleRow1_4 PACCI",
        "Cumulative Amount this Election CycleRow2_4 PACCI",
        "Cumulative Amount this Election CycleRow3_4 PACCI",
        "Cumulative Amount this Election CycleRow4_4 PACCI",
        "Cumulative Amount this Election CycleRow5_4 PACCI",
    ]
    for i, row in enumerate(rows[:5]):
        sfx = suffixes[i]
        fields.extend([
            {"field_id": f"Committee Name{sfx}", "page": page, "value": row["name"], "description": f"PAC row {i+1} name"},
            {"field_id": amount_keys[i], "page": page, "value": fmt(row["amount"]), "description": f"PAC row {i+1} amount"},
            {"field_id": cum_period_keys[i], "page": page, "value": fmt(row["amount"]), "description": f"PAC row {i+1} cum period"},
            {"field_id": cum_cycle_keys[i], "page": page, "value": fmt(row["amount"]), "description": f"PAC row {i+1} cum cycle"},
            {"field_id": f"Street Address{addr_suffixes[i]}", "page": page, "value": row["address"], "description": f"PAC row {i+1} address"},
            {"field_id": f"City{addr_suffixes[i]}", "page": page, "value": row["city"], "description": f"PAC row {i+1} city"},
            {"field_id": f"State{addr_suffixes[i]}", "page": page, "value": row["state"], "description": f"PAC row {i+1} state"},
            {"field_id": f"ZIP{addr_suffixes[i]}", "page": page, "value": row["zip"], "description": f"PAC row {i+1} zip"},
            {"field_id": f"Committee ID Number{cid_suffixes[i]}", "page": page, "value": row.get("fec_id", ""), "description": f"PAC row {i+1} committee ID"},
            {"field_id": f"Date Contribution Received{date_suffixes[i]}", "page": page, "value": row["date"], "description": f"PAC row {i+1} date"},
        ])
    total = sum(r["amount"] for r in rows)
    fields.extend([
        {"field_id": "suma1e", "page": page, "value": fmt(total), "description": "PAC page subtotal"},
        {"field_id": "Cumulative Amount this Reporting PeriodEnter total only if last page of schedule transfer the total received this period to Summary of Receipts line 1e PACCI",
         "page": page, "value": fmt(total), "description": "A(1)(e) period total"},
        {"field_id": "Cumulative Amount this Election CycleEnter total only if last page of schedule transfer the total received this period to Summary of Receipts line 1e PACCI",
         "page": page, "value": fmt(total), "description": "A(1)(e) cycle total"},
        {"field_id": "Text128", "page": page, "value": "1", "description": "page x"},
        {"field_id": "Text129", "page": page, "value": "1", "description": "page of y"},
    ])
    return fields


def _build_inkind_schedule_page(rows, page=22):
    """Page 22: In-kind contributions. Amount fields use .0-.4 row indices."""
    fields = []
    name_suffixes = ["_21", "_22", "_23", "_24", "_25"]
    date_suffixes = ["", "_2", "_3", "_4", "_5"]
    addr_suffixes = ["_76", "_77", "_78", "_79", "_80"]
    occ_suffixes = ["_16", "_17", "_18", "_19", "_20"]
    for i, row in enumerate(rows[:5]):
        fields.extend([
            {"field_id": f"Name{name_suffixes[i]}", "page": page, "value": row["name"], "description": f"In-kind row {i+1} name"},
            {"field_id": f"Date InKind Contribution Received{date_suffixes[i]}", "page": page, "value": row["date"], "description": f"In-kind row {i+1} date"},
            {"field_id": f"Amount Received 1 In-kind Indiv Contr.{i}", "page": page, "value": fmt(row["amount"]), "description": f"In-kind row {i+1} amount"},
            {"field_id": f"Cumulative Amount this Reporting Period 1 In-kind Indiv Contr.{i}", "page": page, "value": fmt(row["amount"]), "description": f"In-kind row {i+1} cum period"},
            {"field_id": f"Cumulative Amount this Election CycleRow1_13 In-kind Indiv Contr.{i}", "page": page, "value": fmt(row["amount"]), "description": f"In-kind row {i+1} cum cycle"},
            {"field_id": f"Street Address{addr_suffixes[i]}", "page": page, "value": row["address"], "description": f"In-kind row {i+1} address"},
            {"field_id": f"City{addr_suffixes[i]}", "page": page, "value": row["city"], "description": f"In-kind row {i+1} city"},
            {"field_id": f"State{addr_suffixes[i]}", "page": page, "value": row["state"], "description": f"In-kind row {i+1} state"},
            {"field_id": f"ZIP{addr_suffixes[i]}", "page": page, "value": row["zip"], "description": f"In-kind row {i+1} zip"},
            {"field_id": f"Occupation{occ_suffixes[i]}", "page": page, "value": row.get("occupation", ""), "description": f"In-kind row {i+1} occupation"},
            {"field_id": f"Employer{occ_suffixes[i]}", "page": page, "value": row.get("employer", ""), "description": f"In-kind row {i+1} employer"},
        ])
    total = sum(r["amount"] for r in rows)
    fields.extend([
        {"field_id": "suma5", "page": page, "value": fmt(total), "description": "In-kind page subtotal"},
        {"field_id": "Cumulative Amount this Reporting PeriodEnter total only if last page of schedule transfer the total received this period to Summary of Receipts line 5a",
         "page": page, "value": fmt(total), "description": "A(5) period total"},
        {"field_id": "Cumulative Amount this Election CycleEnter total only if last page of schedule transfer the total received this period to Summary of Receipts line 5a",
         "page": page, "value": fmt(total), "description": "A(5) cycle total"},
        {"field_id": "Text105", "page": page, "value": "1", "description": "page x"},
        {"field_id": "Text106", "page": page, "value": "1", "description": "page of y"},
    ])
    return fields


def _build_b1_schedule_page(rows, page=40, force_grand_total=None, page_of=(1, 1)):
    """Page 40: Schedule B(1) Operating Expenses. b1_1 through b1_5 amounts.

    force_grand_total: if provided, used in place of page subtotal for the
        'transfer to Summary' line (so the Summary line 1 reflects ALL B(1) rows
        even when only the top 5 fit on the printed page).
    page_of: (this_page, total_pages) → fills Text74/Text75.
    """
    fields = []
    name_suffixes = ["_61", "_62", "_63", "_64", "_65"]
    addr_suffixes = ["_156", "_157", "_158", "_159", "_160"]
    date_suffixes = ["", "_2", "_3", "_4", "_5"]
    cash_keys = ["Cash", "Cash_2", "Cash_3", "Cash_4", "Cash_5"]
    type_suffixes = ["", "_2", "_3", "_4", "_5"]
    cum_period_keys = [
        "Cumulative Amount this Reporting PeriodCash Credit DOE",
        "Cumulative Amount this Reporting PeriodCash Credit_2 DOE",
        "Cumulative Amount this Reporting PeriodCash Credit_3 DOE",
        "Cumulative Amount this Reporting PeriodCash Credit_4 DOE",
        "Cumulative Amount this Reporting PeriodCash Credit_5 DOE",
    ]
    cum_cycle_keys = [
        "Cumulative Amount this Election CycleCash Credit1 DOE",
        "Cumulative Amount this Election CycleCash Credit_2 DOE",
        "Cumulative Amount this Election CycleCash Credit_3 DOE",
        "Cumulative Amount this Election CycleCash Credit_4 DOE",
        "Cumulative Amount this Election CycleCash Credit_5",
    ]
    for i, row in enumerate(rows[:5]):
        fields.extend([
            {"field_id": f"Name{name_suffixes[i]}", "page": page, "value": row["name"], "description": f"B1 row {i+1} payee"},
            {"field_id": f"Disbursement Date{date_suffixes[i]}", "page": page, "value": row["date"], "description": f"B1 row {i+1} date"},
            {"field_id": f"b1_{i+1}", "page": page, "value": fmt(row["amount"]), "description": f"B1 row {i+1} amount"},
            {"field_id": cum_period_keys[i], "page": page, "value": fmt(row["amount"]), "description": f"B1 row {i+1} cum period"},
            {"field_id": cum_cycle_keys[i], "page": page, "value": fmt(row["amount"]), "description": f"B1 row {i+1} cum cycle"},
            {"field_id": f"Street Address{addr_suffixes[i]}", "page": page, "value": row["address"], "description": f"B1 row {i+1} address"},
            {"field_id": f"City{addr_suffixes[i]}", "page": page, "value": row["city"], "description": f"B1 row {i+1} city"},
            {"field_id": f"State{addr_suffixes[i]}", "page": page, "value": row["state"], "description": f"B1 row {i+1} state"},
            {"field_id": f"ZIP{addr_suffixes[i]}", "page": page, "value": row["zip"], "description": f"B1 row {i+1} zip"},
            {"field_id": cash_keys[i], "page": page, "value": "/On", "description": f"B1 row {i+1} cash checkbox"},
            {"field_id": f"Type of Operating Expense Paid{type_suffixes[i]}", "page": page, "value": row["category"], "description": f"B1 row {i+1} expense type"},
        ])
    page_subtotal = sum(r["amount"] for r in rows)
    transfer_total = force_grand_total if force_grand_total is not None else page_subtotal
    fields.extend([
        {"field_id": "sumb1", "page": page, "value": fmt(page_subtotal), "description": "B(1) page subtotal"},
        {"field_id": "Cumulative Amount this Reporting PeriodEnter total only if last page of schedule transfer the total disbursed this period to Summary of Disbursements line 1",
         "page": page, "value": fmt(transfer_total), "description": "B(1) total to Summary line 1 (incl. supplement)"},
        {"field_id": "Cumulative Amount this Election CycleEnter total only if last page of schedule transfer the total disbursed this period to Summary of Disbursements line 1",
         "page": page, "value": fmt(transfer_total), "description": "B(1) cycle total"},
        {"field_id": "Text74", "page": page, "value": str(page_of[0]), "description": "page x"},
        {"field_id": "Text75", "page": page, "value": str(page_of[1]), "description": "page of y"},
    ])
    return fields


def _build_b10_schedule_page(rows, page=64):
    """Page 64: Schedule B(10) Joint Fundraising / Shared Expense Payments."""
    fields = []
    name_suffixes = ["_76", "_77", "_78", "_79", "_80"]
    payment_date_sfx = ["_11", "_12", "_13", "_14", "_15"]
    addr_suffixes = ["_272", "_273", "_274", "_275", "_276"]
    cash_keys = ["Cash_48", "Cash_49", "Cash_50", "Cash_51", "Cash_52"]
    event_date_sfx = ["_6", "_7", "_8", "_9", "_10"]
    expense_type_sfx = ["_6", "_7", "_8", "_9", "_10"]
    cum_period_keys = [
        "Cumulative Amount this Reporting PeriodCash Credit_48_JF_SE",
        "Cumulative Amount this Reporting PeriodCash Credit_49_JF_SE",
        "Cumulative Amount this Reporting PeriodCash Credit_50_JF_SE",
        "Cumulative Amount this Reporting PeriodCash Credit_51_JF_SE",
        "Cumulative Amount this Reporting PeriodCash Credit_52_JF_SE",
    ]
    cum_cycle_keys = [
        "Cumulative Amount this Election CycleCash Credit_48_JF_SE",
        "Cumulative Amount this Election CycleCash Credit_49_JF_SE",
        "Cumulative Amount this Election CycleCash Credit_50_JF_SE",
        "Cumulative Amount this Election CycleCash Credit_51_JF_SE",
        "Cumulative Amount this Election CycleCash Credit_52_JF_SE",
    ]
    for i, row in enumerate(rows[:5]):
        fields.extend([
            {"field_id": f"Committee Name{name_suffixes[i]}", "page": page, "value": row["name"], "description": f"B10 row {i+1} payee"},
            {"field_id": f"Payment Date{payment_date_sfx[i]}", "page": page, "value": row["date"], "description": f"B10 row {i+1} date"},
            {"field_id": f"b10_{i+1}", "page": page, "value": fmt(row["amount"]), "description": f"B10 row {i+1} amount"},
            {"field_id": cum_period_keys[i], "page": page, "value": fmt(row["amount"]), "description": f"B10 row {i+1} cum period"},
            {"field_id": cum_cycle_keys[i], "page": page, "value": fmt(row["amount"]), "description": f"B10 row {i+1} cum cycle"},
            {"field_id": f"Street Address{addr_suffixes[i]}", "page": page, "value": row["address"], "description": f"B10 row {i+1} address"},
            {"field_id": f"City{addr_suffixes[i]}", "page": page, "value": row["city"], "description": f"B10 row {i+1} city"},
            {"field_id": f"State{addr_suffixes[i]}", "page": page, "value": row["state"], "description": f"B10 row {i+1} state"},
            {"field_id": f"ZIP{addr_suffixes[i]}", "page": page, "value": row["zip"], "description": f"B10 row {i+1} zip"},
            {"field_id": cash_keys[i], "page": page, "value": "/On", "description": f"B10 row {i+1} cash checkbox"},
            {"field_id": f"Date of Joint Fundraising Event if applicable{event_date_sfx[i]}", "page": page, "value": row.get("event_date", ""), "description": f"B10 row {i+1} event date"},
            {"field_id": f"Type of Shared Expense if applicable{expense_type_sfx[i]}", "page": page, "value": row.get("shared_expense_type", row.get("category", "")), "description": f"B10 row {i+1} type"},
        ])
    total = sum(r["amount"] for r in rows)
    fields.extend([
        {"field_id": "sumb10", "page": page, "value": fmt(total), "description": "B(10) page subtotal"},
        {"field_id": "Cumulative Amount this Reporting PeriodEnter total only if last page of schedule transfer the total disbursed this period to Summary of Disbursements line 10",
         "page": page, "value": fmt(total), "description": "B(10) period total"},
        {"field_id": "Cumulative Amount this Election CycleEnter total only if last page of schedule transfer the total disbursed this period to Summary of Disbursements line 10",
         "page": page, "value": fmt(total), "description": "B(10) cycle total"},
        {"field_id": "Text28", "page": page, "value": "1", "description": "page x"},
        {"field_id": "of_4", "page": page, "value": "1", "description": "page of y"},
    ])
    return fields


def _build_b12_schedule_page(rows, page=66):
    """Page 66: Schedule B(12) Outstanding Accounts Payable / Debts Owed BY Committee."""
    fields = []
    name_suffixes = ["_71", "_72", "_73", "_74", "_75"]
    addr_suffixes = ["_282", "_283", "_284", "_285", "_286"]
    type_suffixes = ["", "_2", "_3", "_4", "_5"]
    date_suffixes = ["_6", "_7", "_8", "_9", "_10"]
    for i, row in enumerate(rows[:5]):
        fields.extend([
            {"field_id": f"Name{name_suffixes[i]}", "page": page, "value": row["name"], "description": f"B12 row {i+1} creditor"},
            {"field_id": f"Amount1_OAPDebts.{i}", "page": page, "value": fmt(row["amount"]), "description": f"B12 row {i+1} amount"},
            {"field_id": f"Cumulative Amount this Reporting Period1_OAPDebts.{i}", "page": page, "value": fmt(row["amount"]), "description": f"B12 row {i+1} cum period"},
            {"field_id": f"Cumulative Amount this Election CycleRow1_43_OAPDebts.{i}", "page": page, "value": fmt(row["amount"]), "description": f"B12 row {i+1} cum cycle"},
            {"field_id": f"Street Address{addr_suffixes[i]}", "page": page, "value": row["address"], "description": f"B12 row {i+1} address"},
            {"field_id": f"City{addr_suffixes[i]}", "page": page, "value": row["city"], "description": f"B12 row {i+1} city"},
            {"field_id": f"State{addr_suffixes[i]}", "page": page, "value": row["state"], "description": f"B12 row {i+1} state"},
            {"field_id": f"ZIP{addr_suffixes[i]}", "page": page, "value": row["zip"], "description": f"B12 row {i+1} zip"},
            {"field_id": f"Type of Account Payable or Debt Owed{type_suffixes[i]}", "page": page, "value": row["type"], "description": f"B12 row {i+1} type"},
            {"field_id": f"Date that Debt Accrued{date_suffixes[i]}", "page": page, "value": row["date"], "description": f"B12 row {i+1} date accrued"},
        ])
    total = sum(r["amount"] for r in rows)
    fields.extend([
        {"field_id": "sumb12", "page": page, "value": fmt(total), "description": "B(12) page subtotal"},
        {"field_id": "Cumulative Amount this Reporting PeriodEnter total only if last page of schedule transfer the total received this period to Summary of Receipts line 12_2",
         "page": page, "value": fmt(total), "description": "B(12) period total"},
        {"field_id": "Cumulative Amount this Election CycleEnter total only if last page of schedule transfer the total received this period to Summary of Receipts line 12_2",
         "page": page, "value": fmt(total), "description": "B(12) cycle total"},
        {"field_id": "Text25", "page": page, "value": "1", "description": "page x"},
        {"field_id": "of_6", "page": page, "value": "1", "description": "page of y"},
    ])
    return fields


# =============================================================
# Page 3 (Summary of Receipts) and Page 4 (Summary of Disbursements)
# =============================================================

def build_page3_receipts_summary(committee, report_type):
    """Page 3: Summary of Receipts. Columns: Cash, Equity (in-kind / loans / etc.)"""
    is_q1 = report_type == "Q1"
    if is_q1:
        if committee == "John":
            cash_a = 500.00
            cash_b = 1515.00
            cash_c = 68.00
            cash_e = 2000.00
            inkind = 159.70
            cash_total = 4083.00
        else:  # Sara
            cash_a = 500.00
            cash_b = 1110.00
            cash_c = 40.00
            cash_e = 2250.00
            inkind = 159.70
            cash_total = 3900.00
    else:  # pre-election: no receipts
        cash_a = cash_b = cash_c = cash_e = inkind = cash_total = 0.0

    # Outstanding accounts receivable goes to line 10 — we have no AR.
    fields = [
        {"field_id": "CashaInStateIndividualsMorethan100", "page": 3, "value": fmt(cash_a),
         "description": "1(a) cash in-state >$100"},
        {"field_id": "CashbInStateIndividuals100orLessAggregate", "page": 3, "value": fmt(cash_b),
         "description": "1(b) cash in-state ≤$100 aggregate"},
        {"field_id": "CashcOutofStateIndividuals", "page": 3, "value": fmt(cash_c),
         "description": "1(c) cash OOS individuals"},
        {"field_id": "CashePoliticalActionCommittees", "page": 3, "value": fmt(cash_e),
         "description": "1(e) cash from PACs"},
        {"field_id": "CashkMonetaryContributionsSubtotaladd1athrough1j", "page": 3, "value": fmt(cash_a + cash_b + cash_c + cash_e),
         "description": "1(k) Monetary subtotal"},
        {"field_id": "CashmNetMonetaryContributionssubtract1l from1k", "page": 3, "value": fmt(cash_a + cash_b + cash_c + cash_e),
         "description": "1(m) Net monetary"},
        # In-kind on the Equity column (line 5a)
        {"field_id": "Equitya InState Individuals More than 100_2", "page": 3, "value": "0.00",
         "description": "5(a) in-kind individuals >$100"},
        {"field_id": "Equitye Political Action Committees_2", "page": 3, "value": fmt(inkind),
         "description": "5(e) in-kind from PACs (Example Advocacy)"},
        {"field_id": "Equityk InKind Contributions Subtotal equity add 5a through 5j", "page": 3, "value": fmt(inkind),
         "description": "5(k) in-kind subtotal"},
        # Total (line 13)
        {"field_id": "Cash13 Total Receipts cash add 1m 2e 34 89 1112 equity add 2b 5k 67c 1012", "page": 3, "value": fmt(cash_total),
         "description": "13 cash total receipts"},
        {"field_id": "Equity13 Total Receipts cash add 1m 2e 34 89 1112 equity add 2b 5k 67c 1012", "page": 3, "value": fmt(inkind),
         "description": "13 equity total receipts"},
    ]
    return fields


def build_page4_disb_summary(committee, report_type):
    """Page 4: Summary of Disbursements."""
    is_q1 = report_type == "Q1"
    if is_q1:
        if committee == "John":
            line1 = 2339.16  # Operating expenses (B1)
            line10 = 0.00    # Joint fundraising
        else:
            line1 = 2339.11
            line10 = 0.00
        debts = 909.89  # Schedule B(12) outstanding
    else:  # pre-election
        if committee == "John":
            line1 = 910.64  # Example GOTV Vendor $666.66 + Spokes $243.98
            line10 = 0.00
        else:
            line1 = 666.66  # Example GOTV Vendor only
            line10 = 0.00
        debts = 909.89

    cash_total = line1 + line10
    fields = [
        {"field_id": "Cash1 Disbursements for Operating Expenses", "page": 4, "value": fmt(line1),
         "description": "1 Operating expenses"},
        {"field_id": "Cash10 Joint Fundraising  Shared Expense Payments Made", "page": 4, "value": fmt(line10),
         "description": "10 Joint fundraising payments"},
        {"field_id": "Equity12 Outstanding Accounts Payable/Debts Owed by Committee", "page": 4, "value": fmt(debts),
         "description": "12 Outstanding debts owed by committee"},
        {"field_id": "Cash16 Total Disbursements cash add 1 2i 3f 611  1315 equity add 3f 5g  1215", "page": 4, "value": fmt(cash_total),
         "description": "16 cash total disbursements"},
        {"field_id": "Equity16 Total Disbursements cash add 1 2i 3f 611  1315 equity add 3f 5g  1215", "page": 4, "value": fmt(debts),
         "description": "16 equity total (carries debts)"},
    ]
    return fields


def build_all_schedule_fields(committee, report_type):
    """Build all schedule fields (pages 3-69) for one PDF."""
    is_q1 = report_type == "Q1"
    fields = []
    fields += build_page3_receipts_summary(committee, report_type)
    fields += build_page4_disb_summary(committee, report_type)
    fields += build_b12_debts(committee)  # page 66 — applies to both Q1 and pre

    if is_q1:
        fields += build_q1_a1a(committee)  # page 5
        fields += build_q1_a1b(committee)  # page 6
        fields += build_q1_a1c(committee)  # page 7
        fields += build_q1_a1e(committee)  # page 9
        fields += build_q1_a5(committee)   # page 22
        fields += build_b1_q1(committee)   # page 40 (Q1 disbursements)
    else:
        # Pre-election
        if committee == "John":
            fields += build_b1_pre(committee)  # page 40 (Spokes)
        fields += build_b10_pre(committee)     # page 64 (Placeholder reimbursement)

    return fields


if __name__ == "__main__":
    import sys
    committee = sys.argv[1] if len(sys.argv) > 1 else "John"
    report_type = sys.argv[2] if len(sys.argv) > 2 else "Q1"
    fields = build_all_schedule_fields(committee, report_type)
    print(json.dumps(fields, indent=2, default=str))
    print(f"\nTotal fields: {len(fields)}", file=sys.stderr)

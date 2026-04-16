"""Flexible column mapping for user-provided CSV / XLSX files.

Users shouldn't have to copy their data into our exact template. They should
be able to load whatever CSV or XLSX they already have — a Givebutter
export, an ActBlue export, a bank statement, a committee treasurer's
hand-maintained ledger — and have the tool figure out which of their
columns correspond to our required fields.

Design:
  - Every required field has one CANONICAL name plus a list of ALIASES.
  - Aliases are matched case-insensitively, whitespace- and
    punctuation-normalized (so "First Name" matches "first_name", "first-name",
    "FIRST NAME", "firstname").
  - A source file is acceptable if every REQUIRED canonical field can be
    matched to at least one input column. Optional canonical fields are
    matched opportunistically.
  - If multiple input columns match the same canonical, the first wins and
    a warning is surfaced (so the caller can confirm).
  - Unmatched input columns are preserved in a `extras` bucket — nothing is
    silently dropped.
  - The mapper never mutates the user's file on disk. It reads and normalizes.

Usage:

    from openfile_az.column_mapper import detect_donor_columns, MappingResult

    result: MappingResult = detect_donor_columns(headers=df.columns.tolist())
    if not result.is_complete():
        # Surface result.missing to the UI so the user can pick columns.
        ...
    normalized = result.apply(df)  # DataFrame with canonical column names
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import Iterable, Mapping

# ---------------------------------------------------------------------------
# Field definitions — canonical name → (required?, aliases)
# ---------------------------------------------------------------------------

# Each entry: canonical → {"required": bool, "aliases": [variant, variant, ...]}
#
# Aliases should cover:
#   - our own template headers
#   - Givebutter CSV columns
#   - ActBlue CSV columns
#   - NGP VAN fundraising exports
#   - generic bank-statement columns
#   - common spreadsheet conventions
#
# Matching is case-insensitive and normalizes whitespace / punctuation, so
# you only need ONE variant per "shape" of name.

DONOR_FIELDS: Mapping[str, dict] = {
    "date": {
        "required": True,
        "aliases": [
            "date", "transaction date", "transaction date (utc)", "contribution date",
            "received date", "gift date", "donation date", "payment date",
            "timestamp", "date received", "payment captured (utc)",
        ],
    },
    "first": {
        "required": False,   # can be blank for PAC / org donors
        "aliases": [
            "first", "first name", "firstname", "fname", "given name",
            "donor first name", "contact first name",
        ],
    },
    "last": {
        "required": True,
        "aliases": [
            "last", "last name", "lastname", "lname", "surname", "family name",
            "donor last name", "contact last name",
            "donor name", "full name",   # full-name splitting handled downstream
            "name", "entity name", "organization", "organization name",
            "committee name",
        ],
    },
    "address": {
        "required": True,
        "aliases": [
            "address", "street address", "address line 1", "address 1",
            "street 1", "addr1", "address1", "donor addr1", "donor address",
            "donor address line 1", "contact address line 1", "contact address",
        ],
    },
    "address2": {
        "required": False,
        "aliases": [
            "address line 2", "address 2", "street 2", "addr2", "apt", "unit",
            "donor address line 2", "contact address line 2",
        ],
    },
    "city": {
        "required": True,
        "aliases": ["city", "town", "locality", "donor city", "contact city"],
    },
    "state": {
        "required": True,
        "aliases": [
            "state", "state code", "state/province", "province", "region",
            "donor state", "contact state",
        ],
    },
    "zip": {
        "required": True,
        "aliases": [
            "zip", "zip code", "postal code", "postcode", "zipcode", "post code",
            "donor zip", "donor postal code", "contact postal code",
        ],
    },
    "email": {
        "required": False,
        "aliases": [
            "email", "email address", "e-mail", "donor email", "contact email",
        ],
    },
    "occupation": {
        "required": False,
        "aliases": ["occupation", "job title", "title", "donor occupation"],
    },
    "employer": {
        "required": False,
        "aliases": ["employer", "company", "employer name", "donor employer"],
    },
    "source": {
        "required": False,
        # Note: intentionally NOT including "method" here — method is how the
        # money was paid (card / check / ACH), not where it came from.
        "aliases": [
            "source", "campaign", "campaign title", "campaign name", "fundraiser",
            "appeal", "appeal name", "fund", "fund name", "channel",
            "form name",   # ActBlue
        ],
    },
    "amount": {
        "required": True,
        "aliases": [
            "amount", "amount received", "gross amount", "gross", "total",
            "total amount", "donation amount", "contribution amount", "gift amount",
            "amount paid",
        ],
    },
    "kind": {
        "required": False,   # defaults to "cash" if absent
        "aliases": [
            "kind", "contribution type", "gift type", "donation type",
            # NOT "type" or "payment type" alone — too ambiguous, collides w/ method
        ],
    },
    "donor_type": {
        "required": False,   # inferred from presence of pac_id + name shape if absent
        "aliases": [
            "donor type", "contributor type", "entity type", "donortype",
            "contributor category",
        ],
    },
    "pac_id": {
        "required": False,
        "aliases": [
            "pac id", "fec id", "fec committee id", "committee id", "committee id number",
            "az committee id", "filer id",
        ],
    },
    "note": {
        "required": False,
        # "memo" and "description" are here to catch generic bank-export columns,
        # but note the potential collision with disbursement-category fields —
        # disbursement-side aliases exclude them so each field spec stays clean.
        "aliases": [
            "note", "notes", "memo", "description", "comment", "comments",
            "internal note", "public message",
        ],
    },
}


DISBURSEMENT_FIELDS: Mapping[str, dict] = {
    "date": {
        "required": True,
        "aliases": [
            "date", "payment date", "disbursement date", "transaction date",
            "paid date", "check date",
        ],
    },
    "payee": {
        "required": True,
        "aliases": [
            "payee", "vendor", "recipient", "paid to", "name", "beneficiary",
            "payee name", "vendor name",
        ],
    },
    "address": {
        "required": True,
        "aliases": ["address", "street address", "address line 1", "address 1"],
    },
    "city": {"required": True, "aliases": ["city", "town", "locality"]},
    "state": {"required": True, "aliases": ["state", "state code"]},
    "zip": {"required": True, "aliases": ["zip", "zip code", "postal code"]},
    "category": {
        "required": True,
        # Prefer narrow, expense-specific labels. "memo" and "description" are
        # kept here because bookkeeping exports often use them, but a separate
        # dedicated "note" / "memo" column on the same file will win for the
        # "note" canonical, so category gets the GL-style column when one
        # exists.
        "aliases": [
            "category", "expense type", "purpose",
            "gl account", "account", "chart account",
            "type of operating expense paid", "type of expense",
            "memo", "description",
        ],
    },
    "amount": {
        "required": True,
        "aliases": [
            "amount", "total", "paid amount", "amount paid",
            "disbursement amount", "check amount", "payment amount",
        ],
    },
    "schedule": {
        "required": False,    # classifier infers if absent
        "aliases": ["schedule", "az schedule", "form schedule"],
    },
    "payment_method": {
        "required": False,    # defaults to cash
        "aliases": [
            "payment method", "method", "method subtype", "how paid",
            "pay type", "tender", "credit", "credit/cash",
        ],
    },
    "recipient_committee_id": {
        "required": False,
        "aliases": [
            "recipient committee id", "recipient fec id", "fec id",
            "committee id", "payee committee id",
        ],
    },
    "note": {
        "required": False,
        "aliases": ["note", "notes", "memo", "comment", "comments", "internal note"],
    },
}


DEBT_FIELDS: Mapping[str, dict] = {
    "date_incurred": {
        "required": True,
        "aliases": [
            "date incurred", "date", "invoice date", "accrual date",
            "date that debt accrued",
        ],
    },
    "creditor": {
        "required": True,
        "aliases": ["creditor", "vendor", "payee", "owed to", "name"],
    },
    "address": {"required": True, "aliases": ["address", "street address", "address line 1"]},
    "city": {"required": True, "aliases": ["city", "town"]},
    "state": {"required": True, "aliases": ["state", "state code"]},
    "zip": {"required": True, "aliases": ["zip", "zip code", "postal code"]},
    "type_of_debt": {
        "required": True,
        "aliases": ["type of debt", "type", "description", "category"],
    },
    "amount_outstanding": {
        "required": True,
        "aliases": [
            "amount outstanding", "outstanding", "outstanding amount", "amount",
            "balance", "balance due", "unpaid", "owed",
        ],
    },
    "scheduled_payment_date": {
        "required": False,
        "aliases": [
            "scheduled payment date", "expected payment date", "due date", "pay by",
        ],
    },
    "note": {"required": False, "aliases": ["note", "notes", "memo", "comment"]},
}


# ---------------------------------------------------------------------------
# Core matching logic
# ---------------------------------------------------------------------------

_NORMALIZE_RE = re.compile(r"[\s_\-./]+")


def normalize_header(h: str) -> str:
    """Lowercase, strip, collapse whitespace/underscore/hyphen/slash/dot.

    >>> normalize_header("First Name")
    'firstname'
    >>> normalize_header("ADDRESS_LINE-1")
    'addressline1'
    >>> normalize_header(" ZIP/Postal code ")
    'zippostalcode'
    """
    return _NORMALIZE_RE.sub("", (h or "").strip().lower())


@dataclass
class MappingResult:
    """Outcome of attempting to map a source file's headers to our canonicals.

    Attributes:
        mapping: dict of canonical → source column name. Ready-to-apply.
        missing: canonical names whose REQUIRED flag is True but no input
            column matched. If non-empty, the input should be rejected
            or a manual picker should be shown.
        ambiguous: dict of canonical → list of candidate input columns, when
            more than one input column plausibly matched. The first is used
            by default; the UI should let the user confirm or change.
        extras: input column names that didn't match any canonical.
        unknown_required: True if any required canonical is missing.
        field_spec: the field-definition dict (DONOR_FIELDS, DISBURSEMENT_FIELDS,
            DEBT_FIELDS) used to produce this result. Useful for rendering a
            manual-mapping UI that lists the full target schema.
    """
    mapping: dict[str, str] = field(default_factory=dict)
    missing: list[str] = field(default_factory=list)
    ambiguous: dict[str, list[str]] = field(default_factory=dict)
    extras: list[str] = field(default_factory=list)
    field_spec: Mapping[str, dict] = field(default_factory=dict)

    def is_complete(self) -> bool:
        return not self.missing

    def apply(self, df):
        """Return a new DataFrame with columns renamed to canonicals.

        Columns not in the mapping are dropped. Unmatched canonicals are
        added as empty columns so downstream code always sees the full
        schema. Caller is responsible for handling values (type coercion,
        whitespace trim, full-name splitting) downstream.
        """
        import pandas as pd
        out = pd.DataFrame()
        for canonical, src_col in self.mapping.items():
            out[canonical] = df[src_col]
        # Add missing optional columns as empty so downstream code
        # can assume the full schema.
        for canonical, spec in self.field_spec.items():
            if canonical not in out.columns:
                out[canonical] = ""
        return out


def detect_columns(
    headers: Iterable[str],
    field_spec: Mapping[str, dict],
    user_overrides: Mapping[str, str] | None = None,
) -> MappingResult:
    """Match a file's headers against a field-spec dict.

    user_overrides: optional dict of {canonical: source_column}. Wins over
    automatic detection. Use this after the user manually picks a column
    from the UI for an ambiguous / missing canonical.
    """
    headers = [h for h in headers if h is not None]
    user_overrides = user_overrides or {}

    # Normalized lookup: normalized_header → original header
    # (If two headers normalize to the same string — unusual — first wins.)
    by_norm: dict[str, str] = {}
    for h in headers:
        n = normalize_header(h)
        by_norm.setdefault(n, h)

    mapping: dict[str, str] = {}
    ambiguous: dict[str, list[str]] = {}
    for canonical, spec in field_spec.items():
        # User override takes absolute precedence
        if canonical in user_overrides and user_overrides[canonical] in headers:
            mapping[canonical] = user_overrides[canonical]
            continue

        matches = []
        for alias in spec["aliases"]:
            n_alias = normalize_header(alias)
            if n_alias in by_norm:
                matches.append(by_norm[n_alias])

        # Deduplicate preserving order
        seen = set()
        unique_matches = []
        for m in matches:
            if m not in seen:
                seen.add(m)
                unique_matches.append(m)

        if unique_matches:
            mapping[canonical] = unique_matches[0]
            if len(unique_matches) > 1:
                ambiguous[canonical] = unique_matches

    missing = [
        canonical for canonical, spec in field_spec.items()
        if spec["required"] and canonical not in mapping
    ]

    used_source_cols = set(mapping.values())
    extras = [h for h in headers if h not in used_source_cols]

    return MappingResult(
        mapping=mapping,
        missing=missing,
        ambiguous=ambiguous,
        extras=extras,
        field_spec=field_spec,
    )


# Convenience wrappers for each of the three input categories.
def detect_donor_columns(headers, user_overrides=None) -> MappingResult:
    return detect_columns(headers, DONOR_FIELDS, user_overrides)


def detect_disbursement_columns(headers, user_overrides=None) -> MappingResult:
    return detect_columns(headers, DISBURSEMENT_FIELDS, user_overrides)


def detect_debt_columns(headers, user_overrides=None) -> MappingResult:
    return detect_columns(headers, DEBT_FIELDS, user_overrides)


__all__ = [
    "MappingResult",
    "normalize_header",
    "detect_columns",
    "detect_donor_columns",
    "detect_disbursement_columns",
    "detect_debt_columns",
    "DONOR_FIELDS",
    "DISBURSEMENT_FIELDS",
    "DEBT_FIELDS",
]

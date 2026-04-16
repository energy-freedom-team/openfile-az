# Contributing to openfile-az

Thanks for your interest in making Arizona campaign-finance filings less painful.

## Ground rules

- **AZ-specific by design.** This project intentionally does not abstract over states. If you want multi-state support, fork and rename — we'd rather keep this one sharp.
- **Privacy-first.** Any change that sends donor data to an external server is rejected. The hosted web version must always be able to run with the device offline after page load.
- **No legal advice.** Docs and error messages should avoid anything that reads as compliance guidance. "The classifier put this row on A(1)(b)" is fine; "you must file this by X" is not.

## Development setup

```bash
git clone https://github.com/energy-freedom-team/openfile-az.git
cd openfile-az
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Run tests:

```bash
pytest
```

Lint:

```bash
ruff check .
```

## Project structure

```
openfile_az/
├── __init__.py              Version + AZ form revision constants
├── pdf_filler.py            AcroForm field writer (low-level)
├── schedule_builder.py      Per-schedule field generators
├── signer.py                Signature overlay (cursive or PNG)
├── supplement.py            Excel supplements for schedule overflow
├── templates.py             XLSX input templates for users
├── cli.py                   `openfile-az` entry point
└── data/
    ├── AZ_SOS_blank.pdf     Official blank form (AZ SOS rev 9/29/2025)
    └── field_info.json      Extracted field metadata (id, page, rect, type)

tests/
└── golden/                  Known-good output bytes for regression tests

web/                         Pyodide-based browser app (v0.2)
examples/                    Sample config + filled-out templates
```

## Handling AZ form updates

When the Arizona Secretary of State publishes a new revision of the form:

1. Drop the new blank PDF into `openfile_az/data/AZ_SOS_blank.pdf` alongside the old one (rename the old one `AZ_SOS_blank_<rev-date>.pdf`).
2. Re-extract field metadata: `python -m openfile_az.extract_fields`.
3. Diff the resulting `field_info.json` against the previous version — look for renamed or reorganized fields.
4. Update `schedule_builder.py` field ID constants as needed.
5. Bump `__az_form_revision__` in `__init__.py`.
6. Run the golden-file tests against the new form to confirm unchanged schedules still emit correctly.
7. Cut a release.

## Pull requests

- Keep PRs small and focused.
- Add or update tests for any behavior change.
- Sign your commits (`git commit -s`).
- If adding a schedule that's not yet supported, open an issue first so we can discuss the data model.

## Reporting filing errors

If a generated PDF was rejected by the AZ SOS or contains incorrect data:

1. **Do not paste donor PII in the issue.** Redact names, addresses, and amounts.
2. Include the SOS rejection message verbatim.
3. Describe the pattern (e.g., "any PAC donor with a 9-character FEC ID gets misclassified").

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

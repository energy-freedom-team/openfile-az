"""openfile-az CLI — generate, sign, and init campaign finance filings.

Commands:
    openfile-az init              Create example config + spreadsheet templates here
    openfile-az generate          Build PDFs (and Excel supplements) from config
    openfile-az sign              Stamp signatures onto generated PDFs
    openfile-az --version         Print version + AZ form revision
"""
from __future__ import annotations
import argparse
import shutil
import sys
from pathlib import Path

from . import __version__, __az_form_revision__


def _pkg_data(name: str) -> Path:
    return Path(__file__).parent / "data" / name


def cmd_init(args: argparse.Namespace) -> int:
    """Drop example config + sample spreadsheets into the current directory."""
    dest = Path(args.dir).resolve()
    dest.mkdir(parents=True, exist_ok=True)
    # Sample config
    sample_config = dest / "committee_config.yaml"
    if sample_config.exists() and not args.force:
        print(f"refusing to overwrite {sample_config} (pass --force)")
        return 1
    sample_config.write_text(_sample_config_yaml())
    print(f"wrote {sample_config}")
    # Future: also copy example donors.xlsx / disbursements.xlsx templates
    print("\nNext steps:")
    print(f"  1. Edit {sample_config.name} with your committee info")
    print("  2. Fill out donors.xlsx and disbursements.xlsx")
    print(f"  3. Run: openfile-az generate --config {sample_config.name}")
    return 0


def cmd_generate(args: argparse.Namespace) -> int:
    """Build PDFs from config + spreadsheets."""
    # NOTE: current v0.1 uses the schedule_builder's module-level fixtures.
    # v0.2 will consume config.yaml + donors.xlsx + disbursements.xlsx directly.
    print("openfile-az v0.1 — using bundled example data for this build.")
    print("v0.2 will consume config + spreadsheets dynamically.\n")
    try:
        from . import _reference_orchestrator  # noqa: F401 — runs on import
    except Exception as e:
        print(f"generate failed: {e}", file=sys.stderr)
        return 2
    return 0


def cmd_sign(args: argparse.Namespace) -> int:
    """Stamp signatures onto generated PDFs (cursive text fallback; image if provided)."""
    try:
        from . import signer  # noqa: F401 — runs on import (v0.1 behavior)
    except Exception as e:
        print(f"sign failed: {e}", file=sys.stderr)
        return 2
    return 0


def _sample_config_yaml() -> str:
    return """# openfile-az committee config (example)
#
# Fill this out for each committee you file for. Multiple committees in one
# config are supported — useful if you file jointly fundraised slates.
#
# All dollar amounts are USD. Dates are YYYY-MM-DD.

committees:
  - id: "9999001"                          # Your AZ SOS committee ID number
    name: "Jane Example Election Committee"
    candidate: "Jane Example"
    treasurer: "Jane Example"
    address: "123 Main St, Phoenix AZ 85016"
    office_sought: "Example District 1"
    office_type: "special_district"         # or candidate | legislative | statewide | etc.
    starting_balance_q1: 455.00             # Ending balance from prior filing

# One entry per filing period you want to generate:
reports:
  - committee_id: "9999001"
    period: "Q1"                            # Q1 | Q2 | Q3 | Q4 | pre_election | post_election
    date_range: ["2026-01-01", "2026-03-31"]
    filing_date: "2026-04-15"

# Optional: joint-fundraising split rules so donors are auto-allocated across committees.
joint_fundraising:
  - campaign: "Example Joint Campaign"
    split:
      "9999001": 0.5                        # John gets 50%
      "9999002": 0.5                        # Sara gets 50%
"""


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="openfile-az",
        description=(
            "Generate AZ SOS Committee Campaign Finance Reports from spreadsheets. "
            f"AZ form revision {__az_form_revision__}. "
            "Not affiliated with the Arizona Secretary of State."
        ),
    )
    p.add_argument("--version", action="version",
                   version=f"openfile-az {__version__} (AZ form rev {__az_form_revision__})")
    sub = p.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="Create example config in current directory")
    p_init.add_argument("--dir", default=".", help="Target directory (default: cwd)")
    p_init.add_argument("--force", action="store_true", help="Overwrite existing files")
    p_init.set_defaults(func=cmd_init)

    p_gen = sub.add_parser("generate", help="Build PDFs from config")
    p_gen.add_argument("--config", default="committee_config.yaml", help="Config file path")
    p_gen.add_argument("--out", default="./output/", help="Output directory")
    p_gen.set_defaults(func=cmd_generate)

    p_sign = sub.add_parser("sign", help="Stamp signatures onto generated PDFs")
    p_sign.add_argument("--config", default="committee_config.yaml", help="Config file path")
    p_sign.add_argument("--out", default="./output/", help="Output directory")
    p_sign.set_defaults(func=cmd_sign)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

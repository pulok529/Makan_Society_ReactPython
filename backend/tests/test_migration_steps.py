import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts" / "migration"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.append(str(SCRIPTS_DIR))

from steps import MIGRATION_STEPS


def test_migration_steps_are_defined() -> None:
    keys = [step.key for step in MIGRATION_STEPS]
    assert keys == [
        "users",
        "categories_packages",
        "members",
        "member_packages",
        "billing",
        "messaging",
        "reporting",
    ]

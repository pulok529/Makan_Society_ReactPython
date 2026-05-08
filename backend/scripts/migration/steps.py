from dataclasses import dataclass


@dataclass(frozen=True)
class MigrationStep:
    key: str
    description: str


MIGRATION_STEPS: list[MigrationStep] = [
    MigrationStep("users", "Migrate users and roles from legacy auth tables"),
    MigrationStep("categories_packages", "Migrate categories and packages"),
    MigrationStep("members", "Migrate member profile and nominee data"),
    MigrationStep("member_packages", "Migrate package assignments"),
    MigrationStep("billing", "Migrate billing receipts and rebuild charges"),
    MigrationStep("messaging", "Migrate SMS templates and historical messages"),
    MigrationStep("reporting", "Migrate report profile metadata"),
]

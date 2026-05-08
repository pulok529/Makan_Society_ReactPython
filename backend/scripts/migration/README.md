# Legacy Migration Toolkit

This folder contains idempotent migration scaffolds for moving data from legacy `SocietyDB` tables
into the new normalized schema.

## Current Scripts

- `run_migration.py`: orchestrator entrypoint
- `steps.py`: ordered migration step definitions
- `reconcile.py`: post-migration totals and count checks

## Usage

```powershell
cd backend
python scripts/migration/run_migration.py --dry-run
python scripts/migration/run_migration.py --execute
python scripts/migration/reconcile.py
```

## Safety Rules

- Run `--dry-run` first on a non-production database.
- Steps are designed to be idempotent and skip existing target rows where possible.
- Reconciliation output must be reviewed before cutover.

# Error Log

Last updated: 2026-05-20

## Known Errors

- No confirmed runtime errors are documented yet.

## Findings From Repository Inspection

- `backend/app/modules/messaging/bulksmsbd.py` contains a TODO to verify BulkSMSBD's exact `messages` serialization with a real provider sample before building structured bulk-send objects.
- `Jenkinsfile` reports deployment failure generically with: `Deployment failed. Check build logs and docker compose output.`
- Frontend code contains many user-facing fallback messages such as "Unable to load workspace", "Unable to send SMS", and "Unable to download file"; these are handled UI error messages, not confirmed active bugs.
- Potential Alembic metadata warning: `backend/app/db/models.py` may not import every newer model class used by migrations, so verify before relying on Alembic autogenerate.
- Local AI setup note: LM Studio is installed, but `lms status` reported the local server as OFF during the 2026-05-20 check.
- 2026-05-20 billing validation found a real data drift issue before repair:
  - all `150` active members had `joined_on = NULL` in the modern DB
  - no `Registration Fee` due rows existed
  - only one monthly billing head existed in the active local DB
  - result: pre-repair mismatch count was `150` against the restored legacy SQL rules
- 2026-05-20 note: the first version of `rebuild_billing_from_legacy.py` used an overcounting validator for late joiners; the validator was corrected and the final mismatch count is now `0`.
- 2026-05-20 note: older maintenance/cutover scripts still assumed one `Monthly Subscription` head until they were updated to the two-head dated model.

## Failed Commands

- A PowerShell redirection attempt using `<` with `docker exec` failed during SQL comparison because PowerShell does not support that shell-style redirection syntax.
- Temporary SQL-file execution also hit an encoding/BOM issue during `sqlcmd` input piping; later checks used direct `sqlcmd -Q` and in-app SQLAlchemy validation instead.
- An initial attempt to query the latest backup file dynamically inside `sqlcmd` failed due to T-SQL string concatenation syntax around `RESTORE FILELISTONLY`; the direct exact-file query succeeded.

## Unknown Items

- Unknown: whether Qwen2.5 Coder is currently loaded in LM Studio until `lms ps` or `/v1/models` confirms it.

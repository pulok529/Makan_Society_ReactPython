# Society Management Software - Codex Instructions

## Project Scope

- Project name: Society Management Software.
- This repository is only for the society management project.
- Never mix code, database schema, UI, documentation, or assumptions from the Hospital Management Software project into this repository.
- Treat the legacy ASP.NET MVC Makan project only as a migration/reference source when the task explicitly requires it.

## Start Of Every Task

- Read `docs/PROJECT_STATE.md` and `docs/TASKS.md` before starting each task.
- If the task asks for hybrid/local AI assistance, read `docs/LOCAL_AI_WORKFLOW.md`.
- Before starting work, recommend whether the task should be done in `hybrid` mode or `full Codex` mode, with a short reason.
- If the user says "work on hybrid", use the hybrid workflow from `docs/LOCAL_AI_WORKFLOW.md`.
- If the user says "work on Codex fully" or "full Codex", do the work fully with Codex and do not delegate to local AI.
- If the user does not specify `hybrid` or `full Codex`, ask which mode to use before starting substantive work.
- Inspect only the files needed for the current task.
- Do not scan backups, database dumps, or real member records unless the user explicitly asks and confirms the purpose.
- Do not use real member data in prompts, docs, examples, tests, screenshots, or summaries.
- Use fake/demo examples only when an example is necessary.

## Change Rules

- Do not modify business logic unless the user explicitly asks for implementation work.
- Do not build new features unless the user explicitly asks.
- Do not refactor source code as part of documentation or investigation work.
- Keep changes scoped to the current task.
- Do not touch files outside this repository.
- Do not commit automatically.

## Documentation Memory

- Update the docs after every meaningful task.
- Keep `docs/PROJECT_STATE.md` and `docs/TASKS.md` current enough that a new Codex session can continue without old chat history.
- Record known unknowns clearly instead of guessing.
- Record durable technical decisions in `docs/DECISIONS.md`.
- Record known errors, failed commands, and unresolved runtime issues in `docs/ERROR_LOG.md`.

## Output Style After Each Task

When finishing work, respond with:

- What changed
- Files modified
- Commands to run/test
- Remaining issues

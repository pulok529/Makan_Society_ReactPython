# Local AI Workflow

Last updated: 2026-05-20

## Purpose

This project can use a hybrid workflow:

- Codex remains the main engineering agent.
- The local AI model is used for safe draft-only assistance.
- Codex verifies local AI output before using it.
- Real member data, secrets, `.env` values, backups, and database dumps must never be sent to the local AI model.

## Work Mode Selection Rule

Before starting any substantive work, Codex should recommend one of these modes:

- `hybrid`: Codex coordinates and verifies while the local AI model helps with safe draft-only subtasks.
- `full Codex`: Codex does all work directly without local AI delegation.

Mode selection rules:

- If the user says "work on hybrid", use `hybrid`.
- If the user says "work on Codex fully" or "full Codex", use `full Codex`.
- If the user does not specify a mode, Codex must ask which mode to use before starting substantive work.
- For tiny clarification replies or status-only answers, Codex can answer directly, but should still recommend a mode before doing real project work.

Default recommendation guidance:

- Recommend `full Codex` for code changes, migrations, security/auth work, production deployment, tests, builds, and final decisions.
- Recommend `hybrid` for documentation drafts, summaries, checklists, fake/demo examples, wording, and non-sensitive first-pass analysis.
- Even in `hybrid`, Codex owns final verification and file edits.

## Detected Local Setup

Detected on 2026-05-20:

- LM Studio installed: `C:\Users\Pulak\AppData\Local\Programs\LM Studio\LM Studio.exe`
- LM Studio CLI available: `lms`
- LM Studio model root exists: `C:\Users\Pulak\.lmstudio\models`
- Local server status during check: OFF
- OpenAI-compatible API endpoint expected when server is on: `http://localhost:1234/v1`
- Port `1234` was not listening during the check.

Detected models:

- `qwen2.5-coder-14b-instruct`
- `google/gemma-3-4b`
- `text-embedding-nomic-embed-text-v1.5`

Detected tools:

- `curl.exe`
- `node`
- `python`
- `docker`
- `lms`

## Detected PC Configuration

Detected on 2026-05-20:

- PC: Lenovo 82JQ
- OS: Windows 11 Home
- CPU: AMD Ryzen 7 5800H with Radeon Graphics
- CPU cores/threads: 8 cores, 16 logical processors
- RAM: about 27.86 GB
- GPU 1: NVIDIA GeForce RTX 3070 Laptop GPU
- GPU 2: AMD Radeon(TM) Graphics
- Windows reported adapter RAM: 4 GB for each GPU. Confirm actual NVIDIA VRAM in Task Manager or LM Studio because Windows WMI can report laptop GPU memory inaccurately.
- Free space on C drive during check: about 91 GB

This is enough for local AI drafting with Qwen2.5-Coder-14B-Instruct quantized GGUF. Keep expectations realistic: it should help with summaries, documentation drafts, and review checklists, while Codex should still own final code changes and verification.

## Start And Check LM Studio Server

Start LM Studio local server:

```powershell
lms server start
```

Check status:

```powershell
lms status
```

List downloaded models:

```powershell
lms ls
```

List loaded models:

```powershell
lms ps
```

Load the Qwen coder model if needed:

```powershell
lms load qwen2.5-coder-14b-instruct
```

Verify the OpenAI-compatible API:

```powershell
curl.exe http://localhost:1234/v1/models
```

## Codex Delegation Rules

Codex should handle directly:

- Business logic changes.
- Database schema and migration decisions.
- Security, authentication, authorization, and secret handling.
- Final architecture decisions.
- File edits.
- Test/build execution.
- Verification of local AI output.
- Updates to project memory docs.

Local AI may help with:

- Drafting documentation.
- Summarizing non-sensitive source files.
- Creating fake/demo examples.
- Brainstorming UI labels or report wording.
- First-pass checklists.
- First-pass code explanations.
- Reviewing docs for clarity.

Local AI must not receive:

- Real member data.
- Database backup contents.
- `.env` values.
- Passwords, tokens, API keys, or connection strings.
- Private deployment secrets.
- Large unrelated file dumps.
- Hospital Management Software assumptions or content.

## Recommended Prompt Pattern

Use the local model as a junior drafting assistant, not as the final authority.

Example safe local AI prompt:

```text
You are helping draft documentation for the Society Management Software project.
Use only the context below.
Do not invent facts.
Mark unknowns as Unknown.
Do not include real member data.

Task:
Summarize this module for documentation.

Context:
<paste only the relevant non-sensitive code or summary>
```

## PowerShell API Example

Use this only after `lms server start` and after a model is loaded.

```powershell
$body = @{
  model = "qwen2.5-coder-14b-instruct"
  messages = @(
    @{
      role = "system"
      content = "You draft safe project documentation. Do not invent facts. Mark unknowns as Unknown."
    },
    @{
      role = "user"
      content = "Draft a short checklist for validating a FastAPI route. Use fake/demo examples only."
    }
  )
  temperature = 0.2
  top_p = 0.9
  max_tokens = 1000
} | ConvertTo-Json -Depth 10

Invoke-RestMethod `
  -Uri "http://localhost:1234/v1/chat/completions" `
  -Method Post `
  -ContentType "application/json" `
  -Body $body
```

## Recommended LM Studio Settings

For this project and this PC, start conservative:

- Model: `qwen2.5-coder-14b-instruct`
- Temperature for code/docs accuracy: `0.1` to `0.3`
- Temperature for brainstorming UI labels: `0.5` to `0.7`
- Top P: `0.8` to `0.9`
- Repeat penalty: `1.05` to `1.15`
- Max output tokens for drafts: `800` to `1500`
- Max output tokens for deeper summaries: `1500` to `2500`
- Context length: start with `4096`; try `8192` if stable and memory use is acceptable.
- GPU offload: use as much as LM Studio can fit stably on the NVIDIA GPU.
- Keep only one large model loaded at a time.
- Enable Flash Attention if LM Studio/runtime supports it and output remains stable.

If Qwen feels slow:

- Use `google/gemma-3-4b` for quick rough summaries.
- Keep Qwen for code-aware reasoning and final draft quality.

## Quality Gate Before Codex Uses Local AI Output

Before applying anything from the local model, Codex must check:

- Does it match the actual repository?
- Did it invent routes, files, tables, settings, or business rules?
- Did it include real member data or secrets?
- Did it accidentally mix in another project?
- Is it safe to write into docs or code?
- Does it need a test/build check?

If any answer is uncertain, Codex should inspect the repository and mark unknowns clearly.

## Current Setup Status

Ready:

- LM Studio is installed.
- `lms` CLI is available.
- Qwen2.5 Coder model is downloaded.
- Required command-line tools are available.
- PC hardware is suitable for local draft assistance.

Needs action before local AI delegation:

- Start LM Studio server with `lms server start` or from the LM Studio UI.
- Load `qwen2.5-coder-14b-instruct`.
- Verify `http://localhost:1234/v1/models` responds.

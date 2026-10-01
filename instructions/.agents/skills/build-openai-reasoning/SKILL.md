---
name: build-openai-reasoning
description: Phase 8 — Implement sanitized OpenAI structured reasoning
---

# Phase 8 — Implement sanitized OpenAI structured reasoning

## Required reading

- `16_OPENAI_REASONING.md`
- `29_SECURITY_PRIVACY_AND_SECRETS.md`
- `02_LOCKED_PROPOSED_METHOD.md`

## Execution contract

Create mock and real ReasoningClient adapters, strict SecurityEvent allowlist, structured output schema, prompt-injection-resistant evidence framing, evidence-ID validation, token/latency/cost logging and bounded retries. Tests use the mock client. Real external calls require explicit flag and configured credentials. Never pass hidden ground truth or unverified evidence.

## Completion

Run the phase acceptance checks in `36_PHASE_ACCEPTANCE_GATES.md`, update `31_STATUS.md`, report changed files/commands/tests/artifacts/blockers, and stop before the next phase unless explicitly told to continue.

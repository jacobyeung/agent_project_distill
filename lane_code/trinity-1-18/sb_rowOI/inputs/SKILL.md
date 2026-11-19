---
name: no-archaeology
description: "Reader-first writing rule for papers, weekly updates, reports, any reader-facing document, and every instruction file agents bootstrap from (AGENTS.md, skills, dispatch boilerplate, memory) — never narrate the project's own revision history; a new ruling replaces the old text. Use whenever writing or editing a paper section, figure caption, weekly update, progress report, README, skill, rule file, or recorded user ruling."
---

# No archaeology — don't describe the journey

The reader needs three things: what the system IS, what the evidence SHOWS, and why it
supports the claims. The path we took to get there — what we tried first, what we replaced,
which diagnostic preceded which redesign — informs no one outside the project and actively
hurts: it reads as instability and invites "why trust the final version?"

## Scope

Apply the rule to the text you are writing or to the files the request names. A request about one
file, such as a paper section or a report, edits that file only. Sweep memory or other instruction
files only when the user asks for a sweep.

## The test (apply per sentence)

> Would this sentence inform a reader who never saw our process?

If it only makes sense relative to what we did before — DELETE it. Do not soften it into
politer chronology ("we subsequently refined…"); delete it.

## The banned class (examples, not an exhaustive list)

- "Earlier 13-question diagnostic: …"
- "We originally used X, then switched to Y."
- "A previous version of this table showed …"
- "We first tried …" / "was later replaced by …" / "in an earlier run …"
- Weekly-update variant: recapping superseded intermediate numbers or abandoned approaches
  the reader never needed ("last week's 62.1 became 63.4 after we fixed…" → just report the
  current number and what it means).

## What survives

- **Ablations** — presented as *designed comparisons* ("removing X costs Y points"), never as
  chronology ("we later removed X").
- **Forward-looking status** — pending results, TODO markers tied to queued work.
- **Configuration as plain fact** — state benchmark-specific configuration as plain fact without
  narrating where or how design choices, settings, or hyperparameters were selected, tuned, or fit
  on development splits (unless a single plain disclosure sentence is explicitly required).
- **Mixed passages**: keep the result, stated timelessly; drop the history clause.

## Rulings & instruction files (AGENTS.md, skills, dispatch boilerplate, memory)

When the user sets or changes a ruling (a cap, limit, default, or policy), replace the old ruling in
place; never append to it. Every copy (AGENTS.md, memory notes and their index lines, skills, script
comments) states only the current ruling:

- Delete superseded values and their trail: "raised from …", "Update:", "Correction:",
  "Amendment:", "supersedes …", "no longer", "formerly", "prior policy for the record", and old quotes that carry old values.
- Fold an amendment into the rule's text instead of stacking it under the rule.
- No incident narration inside rules (round numbers, postmortems, "lesson from <date>"). Keep the
  *reason* for a rule in one timeless clause; drop the case file. Ledgers hold history and are
  grep-on-demand.
- Names never carry a value that can change: a note is `gpu-cap`, not `gpu-cap-256`.
- A one-off allowance (for one run, program, night, or deadline) is not a ruling. Keep it in that
  task's brief or ledger row only; never write it into AGENTS.md, memory, or skills as a general rule.
- Grep seeds for instruction files in scope: "supersed", "no longer", "formerly", "historical",
  "RETIRED", "lesson", "incident", "postmortem", "era", "previous".

## For dispatched writers (codex lanes included)

Every lane writing or editing reader-facing text applies this rule and lists any borderline
sentence it KEPT (with a one-clause reason) in its report. Grep seeds for reader-facing text:
"earlier", "originally", "initially", "previous version", "we first", "switched to",
"replaced", "prior version", "used to" — then judge each hit semantically; the rule is about
meaning, not keywords.

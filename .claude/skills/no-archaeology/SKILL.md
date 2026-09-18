---
name: no-archaeology
description: Reader-first writing rule for papers, weekly updates, reports, any reader-facing document, and every instruction file agents bootstrap from (AGENTS.md, skills, dispatch boilerplate, memory) — never narrate the project's own revision history; a new ruling replaces the old text. Use whenever writing or editing a paper section, figure caption, weekly update, progress report, README, skill, rule file, or recorded user ruling.
---

# No archaeology — don't describe the journey

The reader needs three things: what the system IS, what the evidence SHOWS, and why it
supports the claims. The path we took to get there — what we tried first, what we replaced,
which diagnostic preceded which redesign — informs no one outside the project and actively
hurts: it reads as instability and invites "why trust the final version?"

## The test (apply per sentence)

> Would this sentence inform a reader who never saw our process?

If it only makes sense relative to what we did before — DELETE it. Do not soften it into
politer chronology ("we subsequently refined…"); delete it.

## The banned class (examples, not an exhaustive list)

- "Earlier 13-question hard-direction diagnostic: …"
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
- **Required disclosures** — e.g., the single plain sentence stating design choices were made
  on a held-out subset before the final evaluation ran once.
- **Mixed passages**: keep the result, stated timelessly; drop the history clause.

## For instruction files (AGENTS.md, skills, dispatch boilerplate, memory)

The same rule binds the files agents read to bootstrap. An instruction file states the current
rule only:

- A new ruling **replaces** the text of the ruling it contradicts. Never write "supersedes X",
  "no longer", "formerly", "now requires", or list the retired alternatives — delete them.
- No incident narration inside rules (round numbers, dates, "the r854 collapse", "lesson from
  2026-07-25"). Keep the *reason* for a rule in one timeless clause; drop the case file. The
  ledgers hold history and are grep-on-demand.
- A date stamp on the current ruling (`USER-RULING 2026-09-11:`) is fine — it says when the rule
  was set, not what it replaced.
- Retired processes get deleted, not marked RETIRED; a one-line do-not-use pointer survives only
  where agents would otherwise stumble into the old path.
- Grep seeds for the sweep: "supersed", "no longer", "formerly", "historical", "RETIRED",
  "lesson", "incident", "postmortem", "era", "previous".

## For dispatched writers (codex lanes included)

Every lane writing or editing reader-facing text applies this rule and lists any borderline
sentence it KEPT (with a one-clause reason) in its report. Grep seeds for the sweep:
"earlier", "originally", "initially", "previous version", "we first", "switched to",
"replaced", "prior version", "used to" — then judge each hit semantically; the rule is about
meaning, not keywords.

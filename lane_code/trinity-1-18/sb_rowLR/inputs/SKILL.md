---
name: summary
description: "How to write a final summary or progress update for a reader who did not watch the work happen — outcome-first, complete sentences, plain language. Use when asked for a summary, recap, status report, or 'where do things stand', especially after autonomous work."
version: 1.1.0
scope: global
---

# /summary — write the recap for someone who wasn't watching

A final summary is not a continuation of your working thread. If you have been
working for a while without the user watching — overnight, across many tool
calls, or since they last spoke — this message is their **first look at any of
it.** Write it as a re-grounding for a fresh reader, not as the next line of your
own train of thought.

Terse shorthand is fine *between* tool calls — that is you thinking out loud, and
brevity there is good. The final summary is different. Drop the working shorthand
here.

## Structure

1. **Open with the outcome (Headline).** One sentence on what happened or what you
   found. Not the process, not the plan — the result.
2. **What we did & what it means.** Supporting detail in complete sentences,
   leading each bullet with the takeaway and translating statistics into numbers
   people feel (e.g., `"42.8% vs. 36% — about a 7-point gain"`).
3. **Where it stands.** Done / running / blocked, and where the key artifacts live.
4. **Needs your call.** The one or two decisions waiting on the user, each explained
   as if new — do not assume they remember the context.

## Rules

- **Leave your working vocabulary behind.** The terms and labels you built up
  while working are yours, not theirs. Do not reuse a name you coined mid-task
  unless you re-introduce it in plain words.
- **Complete sentences. Spell terms out.** No arrow chains (`a → b → c`), no
  hyphen-stacked compounds (`GPU-safe artifact-contract launcher`), no invented
  shorthand labels.
- **One identifier per plain-language clause.** When you mention a file, a commit,
  a flag, a job id, or any other identifier, give each its own clause that says
  what it is. Write "the commit `0dee4bc`, which adds the two skill files" — not a
  bare hash in a list.
- **Be honest.** Never dress up a null result, a bug, or incomplete work as a clean win.
- **If you must choose between short and clear, choose clear.**

## Quick self-check before sending

- Could someone who saw none of the work follow this without scrolling up?
- Does the first sentence state the result?
- Did I explain every identifier rather than just naming it?
- Did I strip the shorthand I was using a moment ago?

---
name: closed-loop
description: Open or close a row in agent/agentic_information_5.0/CLOSED_LOOP_LEDGER.md with the correct format. Matches the ledger's existing column schema exactly, enforces stating the predicted-flip qids BEFORE retesting, pairs every flip-check with a net A/B delta, and checks the tried-and-rejected list before re-running a NO-GO. Use when starting a fix/hypothesis or recording its verdict.
version: 1.0.0
scope: project
---

# /closed-loop — log a fix/hypothesis or its verdict

Keeps the closed-loop ledger — the highest-authority record of what actually worked —
consistent. The ledger is also the analysis-queue: a `pending` row is a fix waiting to be
implemented and retested, and the autonomous loop drains those first each tick.

## Procedure

1. **Read the local header first.** Open
   `agent/agentic_information_5.0/CLOSED_LOOP_LEDGER.md` and match its column schema exactly:
   ```
   round | fix | certainty | predicted-flip qids | implemented (commit) | retested? | qids actually flipped | net cat delta
   ```
   `certainty` is `HIGH`/`MED`/`LOW`. Honor whatever the current header shows if it has drifted.

2. **Pick a mode:**
   - **Open** (before retesting): fill `round`, `fix`, `certainty`, and — required — the
     **predicted-flip qids stated before running** (the falsifiable prediction: which question
     ids this fix should flip from wrong to right). Set `implemented`/`retested?` to `pending`.
     Leave the actual-flips and net-delta columns `TBD`.
   - **Close** (after retesting): fill `implemented (commit)` with the commit hash, `retested?`,
     `qids actually flipped`, and `net cat delta`. If it's a NO-GO, also add one compact row to
     `agent/agentic_information_5.0/TRIED_AND_REJECTED.md` so nobody re-runs it.

3. **Always pair the flip-check with a net A/B.** A fix can hit every predicted flip yet
   net-regress the category (the blocked path had rescue value). Record both `qids actually
   flipped` AND `net cat delta`; judge the fix by the net delta, not the flips alone.

4. **Guard against repeats.** Before opening a row, scan tried-and-rejected / prior NO-GO rows.
   Don't re-propose a rejected approach without a new argument; state what's new if you do.

5. **Respect run-to-run noise.** A net delta inside the noise floor (500q mean ±2–3,
   `object_abs_distance` ±12) is not a win — say "within noise," don't claim it.

6. **Run the smallest decisive test first** — the single changed category (A/B only that cat),
   not a full 10-category run. Full runs are for gate checks near the threshold or the final
   vote pool.

## Output

The exact markdown row(s) to add or edit, with the column count matching the local header.
Edit the ledger in place; confirm the round label and status used.

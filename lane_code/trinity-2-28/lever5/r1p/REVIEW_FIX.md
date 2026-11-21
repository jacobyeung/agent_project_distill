# Review of the join/funnel population fix (relift.py lines 292-295), 2026-11-21, read-only, trinity-2-28

Verdict: NO-GO until a one-line tightening; the real inputs pass either version, so no result changes.

(1) FAIL (narrow). On synthetic key sets the new check rejects every mismatch the original rejects (extra, missing or renamed
object key; item-level row with stage != U; item-level row for an item absent from the funnel; item-level row combined with
another missing or extra key; empty join) and accepts the documented case. It also accepts one undocumented case: item C joined
both at item level and as object row C:t while C:u is missing. The test `{k.split(':')[0] for k in fk-jk} == item_level`
requires only that each item-level item lose at least one funnel object, not all of them.
Fix: replace that clause with `fk-jk != {k for k in fk if k.split(':')[0] in item_level}` (rejects the mixed case; real files pass).

(2) PASS. JOIN_T1 has 299 unique keys, FUNNEL_T1 objects.t1 has 300. The sets differ only by jk-fk = {vsi590k_045785} and
fk-jk = {vsi590k_045785:table, vsi590k_045785:window}. item_level = {vsi590k_045785}, stage 'U'. No funnel key lacks a colon.
All three sub-checks hold; the original equality fails on this item alone.

(3) PASS. `joins`, `jk`, `fk` and `item_level` appear only on lines 291-294. args.join reappears only on line 355, which hashes
the file into input_sha256. Items, exclusions and cells read `refs`, `rows`, `fobjects` and GT, none of which the fix touches;
line 290 (`fobjects`) is unchanged from the original. The fix changes no item set, exclusion or cell.

(4) FAIL (narrow). The AMENDMENT says "the funnel keys missing from the join are exactly the objects of the item-level join
rows"; the code checks only that their item ids equal the item-level set (see 1). The other two clauses and the vsi590k_045785
account match the code. After the one-line fix above, the text and code agree.

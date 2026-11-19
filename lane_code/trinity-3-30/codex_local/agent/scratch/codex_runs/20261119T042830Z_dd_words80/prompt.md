# Draft 80 new question wordings (write one file, nothing else)

Write exactly one file, `/scratch/jjyeung/orch_n30/dist_diag/wordings_draft/WORDINGS_DRAFT_80.json`: a JSON list of 80 distinct English question templates. Each asks for the absolute distance between two objects, measured between their closest points, in a stated unit. Do not read or search anything outside this directory, use no network, and run nothing heavy.

Each template must:
- contain the placeholders `{a}` and `{b}` (each object, written as "the {a}" and "the {b}") and `{u}` (the unit word, a plural such as "meters", "feet", "inches" or "centimeters"), each exactly once;
- state the closest-point convention explicitly, using one of the words "closest", "nearest" or "nearest point(s)", as in "between their closest points";
- read correctly whichever unit fills `{u}`; do not write "a {u}" and do not put a number in the template;
- be one sentence (a question, or an imperative such as "Give ..."), 8 to 30 words long.

Vary the templates: the verb (measure, give, report, tell, estimate, compute, find, state, what is ...), the order (unit first, objects first, convention first or last), where the unit is named ("in {u}", "{u} only", "expressed as {u}", "using {u}"), formality (plain, formal, casual) and length. Mix in some short ones.

Forbidden: any wording in `FORBIDDEN.json` here (the dev-set wordings and the routed training wording), and anything close to them. Do not copy any wording from a benchmark: invent new phrasings, not copies of VSI-Bench, ReVSI, VSI-590K or other published question templates. Avoid starting with "Measuring from the closest point of each object" and avoid the exact phrases "minimal span", "measurable gap", "measure of space", "linear distance" and "separation distance".

When done, print the count and three examples.

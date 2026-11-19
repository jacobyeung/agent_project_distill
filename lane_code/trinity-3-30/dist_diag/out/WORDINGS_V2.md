# WORDINGS_V2: wording sets for coverage v2 (dist_diag, 2026-11-19; ORCH ORDER 0422Z)

## Split of dev-S1's 21 exact wordings (`SPLIT_V2.json`)

Rule: HELD-OUT = the 5 failing wordings (step-200 call rate under 90%) and the 3 other wordings with the lowest sha256('dist_diag|split|' + wording); TRAIN-DEV = the remaining 10 failing wordings; the remaining 3 other wordings are neither trained nor held out.

- HELD-OUT, 8 wordings; never in any training row; dev-S1 items m 18, ft 16, in 12, cm 16:
  - State the distance from the closest point on the {a} to the nearest point on the {b} in {u}.
  - From the closest points of each object, what's the gap between the {a} and the {b} expressed in {u}?
  - Quantify the shortest space separating the {a} from the {b} in {u}.
  - Using the nearest points, what's the spacing between the {a} and the {b} in {u}?
  - Calculate the minimal span from the {a} to the {b} using their closest points, in {u}.
  - Measuring from the closest points of each, how far apart are the {a} and the {b} in {u}?
  - Express in {u} how far apart the closest points of the {a} and the {b} are.
  - Provide the separation distance between the closest points of the {a} and the {b} in {u}.
- TRAIN-DEV, 10 wordings; 50 rows per unit each; dev-S1 items m 24, ft 26, in 21, cm 9:
  - In {u}, what's the smallest distance between the {a} and the {b} using their closest points?
  - What's the measure of space between the nearest points of the {a} and the {b} expressed in {u}?
  - What's the measurable gap from the nearest point on the {a} to the closest point on the {b} in {u}?
  - How many {u} separate the closest points of the {a} and the {b}?
  - Report the shortest distance measurement between the {a} and the {b} in {u}.
  - What's the linear distance between the nearest points of the {a} and the {b} in {u}?
  - Determine the shortest distance between the {a} and the {b} in {u}.
  - Can you provide the distance separating the nearest points of the {a} and the {b}, measured in {u}?
  - Measured from their nearest points, what's the extent between the {a} and the {b} in {u}?
  - Considering their closest points, what's the separation of the {a} from the {b} in {u}?
- Neither trained nor held out, 3 wordings; dev-S1 items m 1, ft 4, in 0, cm 3:
  - Counting from the closest points, how many {u} lie between the {a} and the {b}?
  - Find the shortest distance between the {a} and the {b} using their closest points, in {u}.
  - Using their nearest points, measure the distance from the {a} to the {b} in {u}.

## NEW wordings (40; 25 rows per unit each)

Codex (gpt-6-astra high) drafted 80; `filter_wordings.py` kept them by the rule in `NEW_WORDINGS_V2.json`. The rule requires {a}, {b} and {u} each once, a closest/nearest word, 8 to 30 words, no forbidden phrase, normalized edit distance of at least 0.40 to every dev-S1 wording and the routed wording, and at least 0.25 to earlier drafts.
Filter counts: drafted 80, near a dev wording 3, near another draft 2, passed 75, chosen 40 (lowest sha256). Minimum distance to a dev wording among the chosen: 0.409.

0. Estimate the absolute gap in {u} when the measurement joins the {a} and the {b} at their closest points.
1. For the {a} and the {b}, what does the gap between their closest points come to, expressed as {u}?
2. What closest-point distance reading in {u} would you record for the {a} and the {b}?
3. Give a reading in {u} for the direct gap joining the {a} and the {b} at their nearest points.
4. For the {a} and the {b}, compute the length of their closest-point connector and return it in {u}.
5. Measure the {a} against the {b} for closest-point spacing, with the answer expressed as {u}.
6. At their nearest points, measure the direct gap linking the {a} and the {b}, and express the result as {u}.
7. What is the length, using {u}, of a segment that links the {a} and the {b} at their nearest points?
8. In {u}, estimate the length of the connector whose endpoints are the closest pair on the {a} and the {b}.
9. Enter the length in {u} of the segment defined by the nearest point pair on the {a} and the {b}.
10. What gap reading do you get in {u} with a ruler directly joining the nearest points of the {a} and the {b}?
11. Please record the physical distance in {u} for the {a} and the {b}, using the mutually nearest pair of points.
12. What is the {a} to the {b} nearest-point gap, expressed as {u}?
13. Between their closest points, what physical distance in {u} needs to be covered to get from the {a} to the {b}?
14. Document the absolute gap for the {a} and the {b} in {u}, taking their closest points as the measurement endpoints.
15. With their closest points as endpoints, give a direct distance reading for the {a} and the {b}, using {u}.
16. What length in {u} would you record for the nearest-point gap defined by the {a} and the {b}?
17. Tell me the {a} to the {b} distance in {u}, taking the nearest point pair as the measurement endpoints.
18. Evaluate the length of the nearest-point connection joining the {a} and the {b}, and express the answer as {u}.
19. Find the {a} to the {b} nearest-point connector length in {u}.
20. Imagine marking the closest points on the {a} and the {b}; report the direct distance between those marks in {u}.
21. Using {u}, give the absolute distance for the {a} and the {b}, selecting their closest points for the measurement.
22. What would you write down in {u} for the {a} to the {b} distance, measured between their closest points?
23. In {u}, state the physical distance obtained with the {a} and the {b} as targets and their nearest points as endpoints.
24. State a value in {u} for the gap joining the nearest point pair on the {a} and the {b}.
25. Report in {u} the length of a straight connector joining the closest points of the {a} and the {b}.
26. Choosing the mutually nearest points on the {a} and the {b}, tell me the length of the direct connector in {u}.
27. If a distance gauge links the {a} and the {b} at their nearest points, what should it display in {u}?
28. For the {a} and the {b}, give a closest-point distance reading in {u}.
29. How much length in {u} would you assign to a segment drawn between the nearest points of the {a} and the {b}?
30. Assign a distance value in {u} to the {a} and the {b} based on the direct segment connecting their closest points.
31. Using {u}, measure the gap bounded by the nearest point pair on the {a} and the {b}.
32. Measure the {a} to the {b} gap at their closest points, using {u} only.
33. Take the {a} and the {b} as endpoints of a closest-point measurement; what is the result in {u}?
34. Taking their closest points as endpoints, estimate the length of the direct link joining the {a} and the {b}, in {u}.
35. Using {u}, what would a straight ruler read across the closest points of the {a} and the {b}?
36. In {u}, find the direct gap associated with the closest point pair belonging to the {a} and the {b}.
37. What reading in {u} belongs on a ruler spanning the {a} and the {b} directly between their closest points?
38. Tell me the nearest-point gap for the {a} and the {b}, using {u}.
39. Give me your estimate in {u} for the direct distance linking the {a} and the {b} at their closest points.

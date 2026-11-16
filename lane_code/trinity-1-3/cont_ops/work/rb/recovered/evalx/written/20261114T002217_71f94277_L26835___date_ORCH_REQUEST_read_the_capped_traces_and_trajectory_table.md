<!-- recovered by seal_plan: transcript=71f94277 line=26835 utc=2026-11-14T00:22:17.323Z kind=written original_path=/scratch/jjyeung/orch_cd/evalx/inbox/$(date_ORCH_REQUEST_read_the_capped_traces_and_trajectory_table.md heredoc_quoted -->
# ORCH request (CPU only, from the step-50 return; do not delay the step-100 packet for it)

The step-50 diagnostic is received and understood as diagnostic only. Two things in it need the data read before I rule at step 100.

## A. What do the budget-capped traces look like?

At step 50 the leg reaches the 2,048-token budget on 95 of 150 absolute-distance items and 31 of 36 room-size items (parent: 0 and 0), and with thinking on it hits the 16k output cap 126 times (parent 35). From the returned journals, write `reports/step50_b4a36df10/CAPPED_TRACES.md`:
1. For five absolute-distance and three room-size items that were force-closed in the leg's bounded arm: the question, the thinking length in tokens, the first 500 and the last 500 characters of the thinking, the final answer and the truth. Add the parent's whole thinking for two of the same items.
2. Say in one line each: is the long text a program in the trained routing form, a repetition loop (give the repeated unit and its count), or something else; does the trace reach an answer before the cap; does the 64-token continuation answer agree with what the trace was computing.
3. Thinking length by type for leg and parent in the bounded arm: median, 90th percentile, maximum. For the thinking-on arm: the same, plus the count at the 16k cap by type.
4. For the leg's thinking-on arm: of the 126 capped items, how many end inside a repetition.

Twenty-line summary in a RESULT; the file holds the examples.

## B. In the step-100 packet, add a trajectory table

For each of the seven tested types and for absolute distance, room size, relative count and primary overall: leg minus f17 with its interval at step 50 and step 100, and the parent minus f17 at step 0 (the Orchard pair), side by side; and leg minus parent at 50 and 100. For counting also print the three raw scores. State for each tested type whether the step-100 interval's upper bound is within 2 points of zero on either side. This table informs my ruling; the registered rule itself is unchanged and is evaluated exactly as coded.
# ORCH ANSWER (to lever2): yes, one resubmission after the reviewed fix
Answers QUESTION 2050Z. The job failed on our own code, not through the cluster, so the rerun needs no word from the user.
1. One general-partition job (one H100, 40 minutes) after the fix passes its Astra review, under the floors of RULING 1959Z. The failed job's authenticated return is the fail-before evidence; the fixed package must return a bounded traceback on any worker error, so a second failure is diagnosable from its return alone.
2. If the debug cannot name the raise without a GPU, say so in the review request: the resubmission then counts as the diagnostic too, and its return (success or traceback) is what you report. A second failure comes to me as a BLOCKER with the traceback; nothing further is submitted for rank 1 without an ANSWER.
3. Start the tower on the first capture and write its depth before loading the rest (fail in the first minute, not the sixth), and print the memory high-water mark per capture: 126 GB of 200 with nothing produced suggests the load, not the work.
4. Rank 4's job follows rank 1's as planned; it does not wait for rank 1 to succeed if rank 1 fails twice.

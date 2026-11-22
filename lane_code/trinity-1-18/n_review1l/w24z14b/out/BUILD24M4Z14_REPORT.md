Built out/admit_test.sh and admit_test.py against verified 945-file tree 9d2bbb8ad209d91e21e56121785f62b0dddf3c8d9f14db8d23daf6dcd1d3591b.
The real decoded kit_n_go/k/c.json stand-in passes native identity and the source-extracted legacy processor branch; it is not prepared v.json.
The native full admit call stops on unavailable staged bytes; five independent preparation/review preconditions fail, so the stand-in exits 1.
Changing only min_pixels to 16384 adds R1_LEGACY_PROCESSOR_PIXELS_MUST_USE_DEFAULTS; the negative exits 1 and final verification passes.
Final runs take 1.29/1.21 seconds, use under 240 MB RSS and one torch thread; sealed tree and inspected kit bytes remain unchanged.
173964 real-v.json execution remains NOT_RUN; use out/ADMIT_TEST_USAGE.md and retain its path/hash, ADMIT.json and admit.log for review.
Evidence: work/build24m4z14/{standin_verified,negative_verified,VERIFICATION.json}; full failures are retained in logs. No borderline prose retained.

# Build 6 decisions

Use the original packet base for three-way integration. Preserve the existing level_basis function byte for byte. Keep simulated GT recovery admission with contracts OFF; require the packet training audit with contracts ON. These defaults preserve earlier behavior while adding the accepted contract.

The packet's supporting comparison fixtures are supplied under `work/contracts_r6/packet_root`. Use those exact text fixtures, retain every assertion, and adapt only paths and execution plumbing. Their staged hashes are in `work/build6/PACKET_INPUTS.json`.

No tested D0 export is supplied. The default init selection is the pinned step-544 fallback, recorded in `out/INIT_INPUT.json`; its missing admission evidence remains missing. A2 receives admission priority. A0 is its fallback, and neither kit is a control.

The full units census has no per-unit breakdown. Report the exact slice frequencies and total registered rows per step. Label any per-unit projection from those slice frequencies GUESS.

For persisted metric reports, the options are keyed values with separate ordering metadata or ordered per-unit rows. Use ordered rows by default: the native canonical JSON writer sorts dictionary keys but preserves list order. Empty unit groups carry a zero count and no score; observed groups require finite scores.

Legacy assertions that name an epoch-specific refusal run explicitly in both epochs: retain the exact old OFF expectation and add the accepted ON expectation. Do not broaden an assertion to accept either result or alter the packet's required exact files. Record these fixture adaptations in `work/build6/TEST_INPUT_ADAPTATIONS.json`.

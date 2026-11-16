# b12_cntapp STATUS (trinity-1-3, lane /scratch/jjyeung/orch_n30/b12_cntapp) — a successor resumes from this file alone
Updated: see `date` stamp at bottom. Brief: orch_n30/briefs/b12_cntapp.md -> briefs/qs/12_count_appearance_rows.md. Events: orch_n30/events/b12_cntapp/. Finish/rotate by 22:30Z.
## Done
- Census: events/b12_cntapp/CENSUS.md + RESULT 1155Z_census (questions 1-3 with defaults: accept ~3.7-5.6K unique new counting pairs + totals; extend to frame-map scenes outside the VQA store; stream priority 15).
- Inputs: v5 scene pins work/v5_scene_pins.json; D0 vocab work/d0_vocab.json; VSI-Bench vocab work/bench_vocab.json; D0 existing pairs work/d0_pairs.json; frame map scene frames work/framemap_scene_frames.json (kit frame map 17aa3e9e at rows_rebuild/work/s0/pull/m3/); ARKit alias token rule v+sha256('rung1 scene arkitscenes/<id>')[:12] (1372/1372 agree) -> work/d3_token_map.json; eligibility per frame-map scene (kit Exclusions dev 969cdb56 + bench 3119aa4a + withheld 634820b4) code/elig.py -> work/ELIGIBILITY_SCENES.json.
## Running
- Governed streams (tier 3, prio 15), tmux b12_ark and b12_scn: code/start_stream.sh + code/reader_ark.py (2,155 ARKit captures: 1,135 pool + 1,020 extension; work/streams_ark_jobs.json) -> work/inputs/ark (+ listings work/inputs/ark_lists, log work/inputs/reader_ark.log); code/reader_scn.py (86 ScanNet scenes: 50 pool + 36 extension; work/streams_scn_jobs.json) -> work/inputs/scn (log work/inputs/scn/reader_scn.log). When each finishes (work/streams/<name>.done): rename /data3/jjyeung/orch_n13_20261026/io_governor/streams/b12_cntapp_<name>.json to .done.<epoch>.
- rows_a2 (same node) builds rasters for 686 scenes (d1 204, d2 482) in /scratch/jjyeung/orch_n30/rows_a2/work/rasters (read-only use by me; never edit).
## Next
1. Row generator code/gen_rows.py on rasters (K1 now; mine and rows_a2's when built). 2. Rasters: builder_cr (work/builder) T1 for ScanNet, gb2 b2.py R1 for ARKit. 3. Tests, samples, packet, mirror.

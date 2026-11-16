Executable lines with no execution evidence. Sources and counts: `out/UNEXECUTED.json`.

This is a coverage census, not a claim that unexecuted GPU or remote branches passed. UNEXPLAINED remains a release blocker.

| File | Lines | Class | Condition |
|---|---|---|---|
| `code/adapter.py` | 36 | error branch with condition | sha(p['path']) != p['sha256'] |
| `code/adapter.py` | 54 | error branch with condition | len(group) < n |
| `code/adapter.py` | 65 | error branch with condition | k != 0 |
| `code/adapter.py` | 66,138-139,146,148-158 | UNEXPLAINED | No test or rehearsal executed this job-source line. |
| `code/adapter.py` | 73 | error branch with condition | len(items) != 450 or len({str(x['id']) for x in items}) != 450 |
| `code/adapter.py` | 76 | error branch with condition | sorted(Counter((x['question_type'] for x in items)).values()) != [50] * 9 |
| `code/adapter.py` | 88 | error branch with condition | sel['schema'] != 'rgb32-selection-v1' or sel['cache_id'] != cache or len(sel['frames']) != 32 or (indices != [k * (sel['total_num_frames'] - 1) // 31 for k in range(32)]) or (sel['fps'] != 24) |
| `code/adapter.py` | 93 | error branch with condition | source.stat().st_size != f['png']['size_bytes'] or sha(source) != h |
| `code/adapter.py` | 134 | error branch with condition | len(set(b['keys'])) != len(b['keys']) or b['keys'] != b['canary'] + b['post_canary'] |
| `code/adapter.py` | 140 | error branch with condition | (b['canary'], b['post_canary']) != (canary, post) or len(tasks) != 450 |
| `code/adapter.py` | 147 | error branch with condition | not logical.is_absolute() |
| `code/engine.py` | 20 | error branch with condition | sys.version_info[:2] != (3, 12) or numpy.__version__ != '2.2.6' |
| `code/engine.py` | 31-34,36-37,39-43,45-48,50-53,55-57 | GPU decode | real restoration, prefill, generation and parity |
| `code/engine.py` | 35 | error branch with condition | load(checked(spec['artifact'])).get('step') != 544 |
| `code/engine.py` | 49 | error branch with condition | own.depth_map is None or own.gravity is None |
| `code/engine.py` | 98-100,102,105-107,209-210,231-232 | UNEXPLAINED | No test or rehearsal executed this job-source line. |
| `code/engine.py` | 101 | error branch with condition | not receipt.is_file() or weights.stat().st_size != 5627166200 |
| `code/engine.py` | 198 | error branch with condition | g.get('binding') != bound['binding'] or g.get('config') != spec['config'] or bool(g.get('synthetic')) != boundary.synthetic |
| `code/engine.py` | 274 | error branch with condition | r['bound'] != bound['binding'] or digest({k: v for k, v in r.items() if k != 'binding'}) != r['binding'] |
| `code/engine.py` | 279 | error branch with condition | c['request_binding'] != r['binding'] or c['geometry'] != r['geometry'] or c['config'] != r['config'] |
| `code/entry.py` | 6,40-43,48,56-57,59-63,71-72 | UNEXPLAINED | No test or rehearsal executed this job-source line. |
| `code/orchard.py` | 20 | error branch with condition | bound['source_sha256'] != family['inputs']['item_sha256'] or bound['media_sha256'] != family['inputs']['media_sha256'] or bound['synthetic'] |
| `code/orchard.py` | 24,27-28,30-36,39-55,57-60,64-66 | Orchard-only staging | inherited allocation or return transport |
| `code/orchard.py` | 25 | error branch with condition | not os.environ.get('SLURM_JOB_ID', '').isdigit() |
| `code/orchard.py` | 26 | error branch with condition | config['seconds'] != 21600 |
| `code/orchard.py` | 29 | error branch with condition | family.get('schema') != 'camera-read-family-v1' |
| `code/orchard.py` | 37 | error branch with condition | plan['missing'] |
| `code/policy.py` | 37 | error branch with condition | refused and (c['response'] != RESPONSE or c.get('original_kind', c.get('kind')) != 'error') |
| `code/proof.py` | 37-39,41-45,47,49-60,62-66 | GPU decode | historical greedy repeats require a card |
| `code/proof.py` | 40 | error branch with condition | 'proof_core' not in spec |
| `code/proof.py` | 46 | error branch with condition | request['adapter_sources'] != N.adapter_sources() |
| `code/proof.py` | 61 | error branch with condition | not P.replay(decoded, geo, None)['byte_equal'] |
| `code/proof_stage.py` | 33-35 | UNEXPLAINED | No test or rehearsal executed this job-source line. |
| `code/report.py` | 30 | UNEXPLAINED | No test or rehearsal executed this job-source line. |
| `code/s0.py` | 107-111,120,124,127,157,164-165,167,169,183-188,207,225,237,239-240,251,253,265-276,282-283,285-292,297-307,311-322,326-327,329,333-346,350-351,353-360,365,369,373,377,382-383,386,393,397-401,408-412,414-418,420-424,426-433,435-445,447,449-455,457-459,461,466-467,473-474,476,481,484,510-511,514-515,517-522,524,542-544,546-548,552-553,558,562,592-599,601-602,613-614,619,627-628,665,677,813-816,818-831,833-837,839-845,847-850,854-856,859-860,865-866,871-873,875-884,887-888,893-898,901,904-907,909-912,915-918,921-928,931,950,954 | UNEXPLAINED | No test or rehearsal executed this job-source line. |
| `code/s0.py` | 308,323,347 | error branch with condition | ex_id in seen |
| `code/s0.py` | 361 | error branch with condition | expected_sha and rec.get('config_sha256') != expected_sha |
| `code/s0.py` | 366 | error branch with condition | expected_arch and rec.get('arch') != expected_arch |
| `code/s0.py` | 370 | error branch with condition | expected_fs and rec.get('frame_source') != expected_fs |
| `code/s0.py` | 374 | error branch with condition | expected_pm and rec.get('prompt_mode') != expected_pm |
| `code/s0.py` | 378 | error branch with condition | expected_tok and rec.get('max_new_tokens') != expected_tok |
| `code/s0.py` | 384 | error branch with condition | len(cfg_shas) > 1 |
| `code/s0.py` | 394,622 | error branch with condition | expected_count > 0 and len(records) != expected_count |
| `code/s0.py` | 402-404,629-631 | error branch with condition | actual_ids != sorted(canon_ids) |
| `code/s0.py` | 908 | error branch with condition | not args.cell_name |
| `code/s1.py` | 9,11-14,16,19,34,43,56,59,63,66-73,75,78,81-85,87-90,92-96,99-102,107-120,123-134,137-138,141,148-153,156-158,163,166-181,184-191,196,198-201,206-211,214,220-226,228-231,237-244,251,253,260,263-266,268-272,274-275,277-278,284-291,294,300-302,304-307,309-312,314-315 | UNEXPLAINED | No test or rehearsal executed this job-source line. |
| `code/s1.py` | 74 | error branch with condition | not rounded.is_finite() |
| `code/s1.py` | 86 | error branch with condition | not decimal_value.is_finite() |
| `code/s1.py` | 91 | error branch with condition | not decimal_values |
| `code/s1.py` | 192-193 | error branch with condition | fallback_fields |
| `code/s1.py` | 308 | error branch with condition | strict |
| `code/s2.py` | 19,21-25,27-30,32-33,35,37-41,48,51,53,410,423,436,449-450,466-467,483-484,500,526,539-540,556,575,590,604,616,630-631,647,663,673,682,691,701,716,726,739-740,756,769,780,791,807,820-821,837,847,852,857,863,871,886,899-900,916,929-932,939-940,943,955,967,970,973,976,981,984-985,988,994-997,1004-1007,1010-1012,1015-1016,1019-1020,1022-1024,1026-1027,1029-1032,1036,1042-1044,1048,1053-1057,1059,1061,1063,1065,1067,1070,1073-1074,1077,1080-1083,1085-1086,1088,1090-1091,1096-1100,1103-1106,1108,1111,1114-1118,1121,1129,1131-1135,1143,1151-1152,1154-1158,1160,1162-1167,1170-1179,1182-1185,1188,1191-1196,1201-1204,1211-1216,1219 | UNEXPLAINED | No test or rehearsal executed this job-source line. |
| `code/s2.py` | 1021 | error branch with condition | not isinstance(evidence, list) or not evidence |
| `code/s2.py` | 1025 | error branch with condition | not isinstance(item, Mapping) |
| `code/s2.py` | 1028 | error branch with condition | item['path'] in seen_paths |
| `code/s2.py` | 1033 | error branch with condition | core._sha256_bytes(core._read_stable_bytes(path)) != item['sha256'] |
| `code/s2.py` | 1045 | error branch with condition | not isinstance(note, str) or not note.strip() |
| `code/s2.py` | 1049 | error branch with condition | POLICY_PENDING_NOTE_MARKER not in note |
| `code/s2.py` | 1058 | error branch with condition | composite['record_type'] != 'composite' |
| `code/s2.py` | 1060 | error branch with condition | composite['aggregation']['schema'] != policy['aggregation_schema'] |
| `code/s2.py` | 1062 | error branch with condition | composite['dataset']['dataset_id'] != policy['dataset_id'] |
| `code/s2.py` | 1064 | error branch with condition | composite['dataset']['sha256'] != policy['dataset_sha256'] |
| `code/s2.py` | 1066 | error branch with condition | composite['scope']['question_count'] != policy['question_count'] |
| `code/s2.py` | 1068 | error branch with condition | set(policy['category_policy']) != set(VSTI_CATEGORIES) |
| `code/s2.py` | 1084 | error branch with condition | not isinstance(index, dict) |
| `code/s2.py` | 1087 | error branch with condition | index['schema_version'] != INDEX_SCHEMA_VSTI |
| `code/s2.py` | 1089 | error branch with condition | index['scorer_id'] != current_scorer_id() |
| `code/s2.py` | 1092 | error branch with condition | not isinstance(nominations, Mapping) or set(nominations) != set(VSTI_ROLE_POLICIES) |
| `code/s2.py` | 1107 | error branch with condition | data != core.canonical_json_bytes(parsed) |
| `code/s2.py` | 1130,1153 | error branch with condition | role not in VSTI_ROLE_POLICIES |
| `code/s2.py` | 1161 | error branch with condition | category not in VSTI_CATEGORIES |
| `code/s2.py` | 1220 | error branch with condition | __name__ == '__main__' |
| `code/s3.py` | 15,17-24,26-28,30,33-36,41,43,45,58,73,89,100,104,108,114,118-120,127-129,132-133,136-139,141-142,145-149,152-161,163,166-167,169-173,176-179,181-184,186-187,189-190,192-196,199-200,202-210,212,215-217,219-220,222,225,231-233,235-236,240,242-243,247,249-253,258,261-262,264-265,267,270-271,273,275-276,278,285-286,289-292,295-297,303-304,308,316,318,321,329-331,340,353-356,359,362-366,368,370,373-377,380-388,397,400-401,420,423,430,434,436-437,439-446,448,450,452,456,459,463-464,466-469,473,490,493,501-502,504-505,508-515,517,519,521-523,525-527,530,532-537,541,555,558,561-579,581,583-587,590-591,593-596,599,605-606,608,610-614,616,620-623,625-626,628-636,638,640,642-646,648-655,657-658,660,662-665,667-668,672-674,676-681,683-684,686-692,694-695,697,699,704,708,710,712-714,716,718-722,724,728-733,735-739,741-742,745-749,751-752,754-756,758,760,762,764,767,770,773-778,781-785,787,791,802,804-810,812-815,817,819,822-824,826,829,832-835,837,839,841,844-852,855-863,866,871-876,879,889-894,896-900,902-907,910-911,913-914,917-919,921,925,936-946,955,957-963,972,979-981,985,987,989,992,996 | UNEXPLAINED | No test or rehearsal executed this job-source line. |
| `code/s3.py` | 140 | error branch with condition | key in result |
| `code/s3.py` | 162 | error branch with condition | before_identity != after_identity or len(data) != after.st_size |
| `code/s3.py` | 168 | error branch with condition | isinstance(value, bool) |
| `code/s3.py` | 180 | error branch with condition | not isinstance(parsed, list) |
| `code/s3.py` | 185 | error branch with condition | not isinstance(item, dict) |
| `code/s3.py` | 188 | error branch with condition | key not in item |
| `code/s3.py` | 191 | error branch with condition | qid in by_qid |
| `code/s3.py` | 201 | error branch with condition | not artifact_dir.is_dir() |
| `code/s3.py` | 211 | error branch with condition | not selected |
| `code/s3.py` | 218 | error branch with condition | not present |
| `code/s3.py` | 221 | error branch with condition | len(values) != 1 |
| `code/s3.py` | 234 | error branch with condition | not isinstance(payload, dict) |
| `code/s3.py` | 237 | error branch with condition | payload_qid != filename_qid |
| `code/s3.py` | 241 | error branch with condition | payload_qid != str(dataset_item['id']) |
| `code/s3.py` | 244 | error branch with condition | payload_category != category |
| `code/s3.py` | 248 | error branch with condition | dataset_item['question_type'] != category |
| `code/s3.py` | 263 | error branch with condition | not isinstance(value, str) or not value |
| `code/s3.py` | 266 | error branch with condition | path.is_absolute() or '.' in path.parts or '..' in path.parts or ('\\' in value) |
| `code/s3.py` | 272 | error branch with condition | source_kind != 'single_run' |
| `code/s3.py` | 274 | error branch with condition | not SOURCE_ID_RE.fullmatch(source_id) |
| `code/s3.py` | 277 | error branch with condition | 'vote' in lowered or 'synthetic' in lowered |
| `code/s3.py` | 298 | error branch with condition | actual != expected |
| `code/s3.py` | 305 | error branch with condition | not isinstance(value, str) or SHA256_RE.fullmatch(value) is None |
| `code/s3.py` | 317 | error branch with condition | isinstance(value, bool) or not isinstance(value, int) or value <= 0 |
| `code/s3.py` | 360 | error branch with condition | not expected |
| `code/s3.py` | 367 | error branch with condition | filename_qid in seen |
| `code/s3.py` | 369 | error branch with condition | filename_qid not in expected |
| `code/s3.py` | 378 | error branch with condition | missing |
| `code/s3.py` | 435 | error branch with condition | len(records) < 2 |
| `code/s3.py` | 438 | error branch with condition | first.get('record_type') != 'category' |
| `code/s3.py` | 447 | error branch with condition | record.get('record_type') != 'category' |
| `code/s3.py` | 449,518 | error branch with condition | record['scorer_id'] != scorer_id |
| `code/s3.py` | 451,524 | error branch with condition | record['dataset'] != dataset |
| `code/s3.py` | 453,520 | error branch with condition | record['scope']['category'] != category |
| `code/s3.py` | 462 | error branch with condition | constituent_count != _require_positive_int(first['scope']['question_count'], 'seed_mean constituent question_count') |
| `code/s3.py` | 465 | error branch with condition | source_id in source_ids |
| `code/s3.py` | 503,734 | error branch with condition | formula is None |
| `code/s3.py` | 506 | error branch with condition | set(category_source_records) != set(categories) |
| `code/s3.py` | 516 | error branch with condition | record_type not in ('category', 'seed_mean') |
| `code/s3.py` | 592 | error branch with condition | not isinstance(dataset, Mapping) |
| `code/s3.py` | 607 | error branch with condition | record['schema_version'] != RECORD_SCHEMA |
| `code/s3.py` | 609 | error branch with condition | record['semantic_integrity'] != 'not_evaluated' |
| `code/s3.py` | 615 | error branch with condition | _record_id(body) != claimed_id |
| `code/s3.py` | 617 | error branch with condition | expected_scorer_id is not None and record['scorer_id'] != expected_scorer_id |
| `code/s3.py` | 624 | error branch with condition | not isinstance(source, Mapping) |
| `code/s3.py` | 627 | error branch with condition | source != _source(source['source_id'], source['artifact_key'], source['kind']) |
| `code/s3.py` | 637 | error branch with condition | not isinstance(traces, list) or not isinstance(scores, list) |
| `code/s3.py` | 639 | error branch with condition | len(traces) != scope['question_count'] or len(scores) != scope['question_count'] |
| `code/s3.py` | 641 | error branch with condition | _sha256_bytes(canonical_json_bytes(traces)) != inputs['set_sha256'] |
| `code/s3.py` | 647 | error branch with condition | trace['basename'] != f'trace_{qid}.json' |
| `code/s3.py` | 656,693 | error branch with condition | not isinstance(value, (int, float)) or isinstance(value, bool) or (not 0 <= value <= 1) |
| `code/s3.py` | 659 | error branch with condition | trace_qids != sorted(trace_qids, key=int) or score_qids != sorted(score_qids, key=int) |
| `code/s3.py` | 661 | error branch with condition | len(set(trace_qids)) != len(trace_qids) or trace_qids != score_qids |
| `code/s3.py` | 666,723 | error branch with condition | score['metric'] != expected_metric |
| `code/s3.py` | 669 | error branch with condition | score['value'] != expected_value |
| `code/s3.py` | 675 | error branch with condition | record['source'] != {'kind': 'seed_mean'} |
| `code/s3.py` | 682 | error branch with condition | aggregation['schema'] != SEED_MEAN_AGGREGATION_SCHEMA |
| `code/s3.py` | 685 | error branch with condition | not isinstance(constituents, list) or len(constituents) < 2 |
| `code/s3.py` | 696 | error branch with condition | loaded.get('record_type') != 'category' |
| `code/s3.py` | 698,761 | error branch with condition | loaded['dataset'] != record['dataset'] |
| `code/s3.py` | 700 | error branch with condition | loaded['scope']['category'] != scope['category'] |
| `code/s3.py` | 705 | error branch with condition | loaded['scope']['question_count'] != scope['question_count'] |
| `code/s3.py` | 709 | error branch with condition | loaded['source']['source_id'] != item['source_id'] |
| `code/s3.py` | 711 | error branch with condition | float(loaded['score']['value']) != float(value) |
| `code/s3.py` | 715 | error branch with condition | len(set(source_ids)) != len(source_ids) |
| `code/s3.py` | 717 | error branch with condition | source_ids != sorted(source_ids) |
| `code/s3.py` | 725 | error branch with condition | score['value'] != scoring.canonical_mean(values) |
| `code/s3.py` | 740 | error branch with condition | scope['categories'] != list(categories) |
| `code/s3.py` | 743 | error branch with condition | not isinstance(category_sources, Mapping) or set(category_sources) != set(categories) |
| `code/s3.py` | 750 | error branch with condition | not isinstance(entry, Mapping) |
| `code/s3.py` | 753 | error branch with condition | entry['record_type'] not in ('category', 'seed_mean') |
| `code/s3.py` | 757 | error branch with condition | loaded.get('record_type') != entry['record_type'] |
| `code/s3.py` | 759 | error branch with condition | loaded['scope']['category'] != category |
| `code/s3.py` | 763 | error branch with condition | loaded['scorer_id'] != record['scorer_id'] |
| `code/s3.py` | 771 | error branch with condition | scope['question_count'] != total_questions |
| `code/s3.py` | 786 | error branch with condition | score['official'] != expected_official |
| `code/s3.py` | 788 | error branch with condition | score['raw_category_macro'] != expected_macro |
| `code/s3.py` | 803 | error branch with condition | not isinstance(record, Mapping) |
| `code/s3.py` | 811,816 | error branch with condition | resolve is None |
| `code/s3.py` | 825 | error branch with condition | match is None |
| `code/s3.py` | 836 | error branch with condition | data != canonical_json_bytes(parsed) |
| `code/s3.py` | 838 | error branch with condition | not isinstance(parsed, dict) |
| `code/s3.py` | 840 | error branch with condition | parsed.get('record_id') != record_id |
| `code/s3.py` | 895 | error branch with condition | loaded['record_type'] != kind |
| `code/s3.py` | 901 | error branch with condition | loaded['source']['artifact_key'] != expected_key |
| `code/s3.py` | 908 | error branch with condition | leaf['source']['artifact_key'] != expected_key |
| `code/s3.py` | 912 | error branch with condition | actual_source_ids != expected_source_ids |
| `code/s3.py` | 920 | error branch with condition | other != first_qids |
| `code/s3.py` | 922 | error branch with condition | _sha256_bytes(canonical_json_bytes(first_qids)) != source_policy['qid_set_sha256'] |
| `code/s3.py` | 956 | error branch with condition | rebuilt != checked_leaf or canonical_json_bytes(rebuilt) != canonical_json_bytes(checked_leaf) |
| `code/s3.py` | 975 | error branch with condition | rebuilt_leaf != leaf_checked or canonical_json_bytes(rebuilt_leaf) != canonical_json_bytes(leaf_checked) |
| `code/s3.py` | 984 | error branch with condition | rebuilt_seed_mean != checked_leaf or canonical_json_bytes(rebuilt_seed_mean) != canonical_json_bytes(checked_leaf) |
| `code/s3.py` | 995 | error branch with condition | rebuilt_composite != checked_composite or canonical_json_bytes(rebuilt_composite) != canonical_json_bytes(checked_composite) |
| `code/scorer.py` | 42 | error branch with condition | mismatches or val != expected or abs(collapsed['primary'] - doc['primary_score']) > 1e-12 |
| `code/sj/orch_cd/evalx/work/milestone/chain_save.py` | 26,65 | error branch with condition | path.is_symlink() |
| `code/sj/orch_cd/evalx/work/milestone/chain_save.py` | 37-39,42,47-49,52,54-56,59,63-64,66-71,76-81,83-87,89-91,93,97-98,100,102-103,105,107-110,112-120,122,127-133,137 | UNEXPLAINED | No test or rehearsal executed this job-source line. |
| `code/sj/orch_cd/evalx/work/milestone/chain_save.py` | 41 | error branch with condition | not path.is_absolute() or not any((resolved.is_relative_to(root) for root in (Path('/scratch'), Path('/tmp'), Path('/dev/shm')))) |
| `code/sj/orch_cd/evalx/work/milestone/chain_save.py` | 53 | error branch with condition | self.written + len(data) > self.limit |
| `code/sj/orch_cd/evalx/work/milestone/chain_save.py` | 72 | error branch with condition | path.exists() |
| `code/sj/orch_cd/evalx/work/milestone/chain_save.py` | 88 | error branch with condition | path.suffix in ('.pt', '.safetensors', '.png', '.jpg', '.jpeg') |
| `code/sj/orch_cd/evalx/work/milestone/chain_save.py` | 92 | error branch with condition | not result |
| `code/sj/orch_cd/evalx/work/milestone/chain_save.py` | 99 | error branch with condition | slot not in (0, 1) or not 0 <= persisted_input_bytes <= PROJECT_LIMIT |
| `code/sj/orch_cd/evalx/work/milestone/chain_save.py` | 101 | error branch with condition | not output.is_dir() |
| `code/sj/orch_cd/evalx/work/milestone/chain_save.py` | 104 | error branch with condition | used + persisted_input_bytes + ARCHIVE_LIMIT > PROJECT_LIMIT |
| `code/sj/orch_cd/evalx/work/milestone/chain_save.py` | 106 | error branch with condition | shutil.disk_usage(output).free < MIN_FREE + ARCHIVE_LIMIT |
| `code/sj/orch_cd/evalx/work/milestone/chain_save.py` | 111 | error branch with condition | target.is_symlink() |
| `code/sj/orch_cd/evalx/work/milestone/chain_save.py` | 121 | error branch with condition | shutil.disk_usage(output).free < MIN_FREE |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/camera_cohort.py` | 1-4,7-8,11-13,15,18-20,23-24,28-29,32-33,36-37,39,42-43,45-46,48,50-51,53-54,56-57,59,61-64,69-70,73 | UNEXPLAINED | No test or rehearsal executed this job-source line. |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/camera_cohort.py` | 14 | error branch with condition | p.parts[1:2] == ('home',) or (len(p.parts) > 1 and p.parts[1].startswith('data')) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/camera_cohort.py` | 38 | error branch with condition | sha(value['path']) != value['sha256'] |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/camera_cohort.py` | 44 | error branch with condition | receipt_pin.get('sha256') != FROZEN_COHORT_SHA |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/camera_cohort.py` | 47 | error branch with condition | receipt.get('schema') != 'legs1-camera-cohort-v1' or receipt.get('frozen') is not True |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/camera_cohort.py` | 49 | error branch with condition | receipt['frames']['sha256'] != frames_pin['sha256'] |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/camera_cohort.py` | 52 | error branch with condition | receipt.get('model_reads_before_freeze') != 0 |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/camera_cohort.py` | 55 | error branch with condition | len(tasks) != 450 or len({t['id'] for t in tasks}) != 450 |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/camera_cohort.py` | 58 | error branch with condition | dict(counts) != {t: 150 for t in TYPES} or dict(counts) != receipt['counts'] |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/camera_cohort.py` | 60 | error branch with condition | digest([t['id'] for t in tasks]) != receipt['ordered_ids_sha256'] |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/camera_cohort.py` | 68 | error branch with condition | task['source_frame_indices'] != capture['anchor_indices'] or task['rgb32_sha256'] != digest(capture['frames']) or task.get('stratum') != 'camera_gt' or (task.get('label_authority') != 'native_camera_gt') |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/camera_cohort.py` | 72 | error branch with condition | not isinstance(pair, list) or len(pair) != 2 or any((type(v) is not int for v in pair)) or (not 1 <= pair[0] < pair[1] <= 32) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/camera_report.py` | 1,3,5-6,9-10,13-25,27-44,47-49,52-58,63-67,70,76-79,83-85,87,90-91,93-94 | UNEXPLAINED | No test or rehearsal executed this job-source line. |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/camera_report.py` | 62 | error branch with condition | shortcut.get('schema') != 'legs1-camera-shortcuts-v1' or shortcut.get('cohort_sha256') != FROZEN_COHORT_SHA or shortcut['tasks']['sha256'] != receipt['tasks']['sha256'] or (set(shortcut['by_id']) != {t['id'] for t in tasks}) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/camera_report.py` | 69 | error branch with condition | (row['question_type'], row['room'], row['stratum']) != (task['question_type'], task['room'], task['stratum']) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/common.py` | 19 | error branch with condition | p.parts[1:2] == ('home',) or (len(p.parts) > 1 and p.parts[1].startswith('data')) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/common.py` | 37-38,42-44 | UNEXPLAINED | No test or rehearsal executed this job-source line. |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/frozen_kit.py` | 18,23,25-26,31-33,35-36 | UNEXPLAINED | No test or rehearsal executed this job-source line. |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/frozen_kit.py` | 24 | error branch with condition | sha(root / 'kit_combo3.tar.gz') != ARCHIVE_SHA |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/frozen_kit.py` | 27 | error branch with condition | sha(root / name) != CODE[name] |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/frozen_kit.py` | 34 | error branch with condition | code != CODE or binding.get('code_sha256') != CODE or dense.get('code_sha256') != CODE |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/frozen_kit.py` | 38 | error branch with condition | type(settings.get('image_batch_size', 1)) is not int or settings.get('image_batch_size', 1) != 1 or settings.get('native_image_batch', False) is not False |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/geometry.py` | 18 | error branch with condition | len(frames) != n or len(slots) != 32 or slots[0] != 0 or (slots[-1] >= n) or (min(slots) < 0) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/geometry.py` | 20 | error branch with condition | any((type(i) is not int for i in indices + slots)) or any(np.diff(indices) <= 0) or any(np.diff(slots) <= 0) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/geometry.py` | 34 | error branch with condition | own_depth.shape != (32, 51, 51) or not np.isfinite(own_depth).all() or np.any(own_depth <= 0) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/geometry.py` | 61 | error branch with condition | m.get('schema') != GR.SCHEMA or m.get('checkpoint') != artifact |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/geometry.py` | 63 | error branch with condition | m.get('producer') != 'legs1-own-scale-gravity-v1' or m.get('producer_sha256') != sha(__file__) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/geometry.py` | 105 | error branch with condition | not args.device.startswith('cuda:') |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/geometry.py` | 106-117,119,121-122,124-137,139,141-148,150-154,159-165,168-169 | GPU decode | inherited card preparation path |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/geometry.py` | 120 | error branch with condition | load(args.export).get('step') != args.step |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/geometry.py` | 138 | error branch with condition | state.frame_indices[state.anchor_slots].tolist() != c['anchor_indices'] |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/geometry.py` | 140 | error branch with condition | own.depth_map is None or own.gravity is None |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/geometry.py` | 172-178 | UNEXPLAINED | No test or rehearsal executed this job-source line. |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/geometry_refusals.py` | 13,20-23,25,27,70-72,78,96,103-105,108,110-111,121,125-127,131-133,136-139,141,148-149,151-154,156-159,164-165,167-176,178,180 | UNEXPLAINED | No test or rehearsal executed this job-source line. |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/geometry_refusals.py` | 24 | error branch with condition | code != NONFATAL_CODE |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/geometry_refusals.py` | 26 | error branch with condition | not isinstance(code, str) or not message |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/geometry_refusals.py` | 39 | error branch with condition | rotations.shape != (32, 3, 3) or head.shape != (3,) or tower.shape != (3,) or (not all((np.isfinite(value).all() for value in (rotations, head, tower)))) or (min(np.linalg.norm(head), np.linalg.norm(tower)) < 1e-06) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/geometry_refusals.py` | 56 | error branch with condition | manifest.get('schema') != SCHEMA or manifest.get('policy') != POLICY or manifest.get('checkpoint') != checkpoint or (not manifest.get('records')) or (not isinstance(manifest.get('videos'), dict)) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/geometry_refusals.py` | 63 | error branch with condition | not isinstance(native, str) or not native or native in names or (not isinstance(clip, str)) or (len(clip) != 64) or (clip in clips) or (record.get('checkpoint') != checkpoint) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/geometry_refusals.py` | 68 | error branch with condition | record.get('error') is not None or not isinstance(record.get('output'), dict) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/geometry_refusals.py` | 76 | error branch with condition | not isinstance(error, dict) or error.get('code') != NONFATAL_CODE or any((not isinstance(error.get(key), str) or not error[key] for key in ('code', 'message', 'exception'))) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/geometry_refusals.py` | 80 | error branch with condition | videos != manifest['videos'] |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/geometry_refusals.py` | 82 | error branch with condition | expected is not None and (len(expected) != len(set(expected)) or names != set(expected)) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/geometry_refusals.py` | 92 | error branch with condition | task['id'] in seen or task['native'] not in by_native |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/geometry_refusals.py` | 107 | error branch with condition | refusal['capture'] != task['native'] or refusal['checkpoint'] != request['artifact'] or perception.get('geometry_refusal') != refusal |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/geometry_refusals.py` | 135 | error branch with condition | len(names) != 84 or len(set(names)) != 84 or any((record['status'] not in ('PASS', 'REFUSED') for record in records)) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/geometry_refusals.py` | 140 | error branch with condition | pilot_names != full_names |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/geometry_refusals.py` | 150 | error branch with condition | len(membership) != len(expected) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/geometry_refusals.py` | 155 | error branch with condition | arm not in observed or key not in membership or key in observed[arm] |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/geometry_refusals.py` | 163 | error branch with condition | refused != bound['geometry_refused'] or type(score) not in (int, float) or (not math.isfinite(score)) or (not 0 <= score <= 1) or (refused and (score != 0 or row.get('called') is not False or row.get('decode_executed') is not False or ('decode' in row))) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/mask_kit/kitlib.py` | 2-24,26-34,36-38,40-41,43,45,49-51,57,59,61-63,65,67,69-70,72-76 | UNEXPLAINED | No test or rehearsal executed this job-source line. |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/mask_kit/kitlib.py` | 25 | error branch with condition | not str(p).startswith('/scratch/') |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/mask_kit/kitlib.py` | 35 | error branch with condition | h <= 0 or w <= 0 or h * w > 4000000 or any((type(v) != int or v < 0 for v in counts)) or (sum(counts) != h * w) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/mask_kit/kitlib.py` | 39 | error branch with condition | not check_manifest(m) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/mask_kit/kitlib.py` | 42 | error branch with condition | c['scene'] in seen or '..' in c['scene'] or len(c['scene'].split('/')) != 2 |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/mask_kit/kitlib.py` | 44 | error branch with condition | len(c['frames']) != 32 or [f['index'] for f in c['frames']] != c['anchor_indices'] or len(set(c['anchor_indices'])) != 32 |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/mask_kit/kitlib.py` | 46 | error branch with condition | f['path'] != f['sha256'][:2] + '/' + f['sha256'] + '.png' |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/mask_kit/kitlib.py` | 47 | error branch with condition | c['phrases'] != sorted(set(c['names'].values())) or any((normalize_phrase(n) != p for n, p in c['names'].items())) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/mask_kit/kitlib.py` | 48 | error branch with condition | m['detect_calls'] != sum((len(c['phrases']) for c in m['captures'])) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/mask_kit/kitlib.py` | 52 | error branch with condition | v.get('contract') != contract |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/mask_kit/kitlib.py` | 53 | error branch with condition | v.get('stub') and (not allow_stub) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/mask_kit/kitlib.py` | 54 | error branch with condition | v['schema'] != SCHEMA or v['manifest_sha256'] != msha or v['scene'] != c['scene'] |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/mask_kit/kitlib.py` | 55 | error branch with condition | v['frame_indices'] != c['anchor_indices'] or v['frame_sha256'] != [f['sha256'] for f in c['frames']] or v['phrases'] != c['phrases'] |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/mask_kit/kitlib.py` | 56 | error branch with condition | set(v['frames']) != {str(k) for k in range(32)} |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/mask_kit/kitlib.py` | 58 | error branch with condition | set(fr['phrases']) != set(c['phrases']) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/mask_kit/kitlib.py` | 60 | error branch with condition | len(r['instances']) > contract['cap'] or not 0 <= r['presence'] <= 1 |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/mask_kit/kitlib.py` | 64 | error branch with condition | not (0 <= s <= 1 and contract['joint_floor'] - 1e-06 <= j <= 1 and (abs(j - s * i.get('source_presence', r['presence'])) < 1e-05) and (s <= last + 1e-06)) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/mask_kit/kitlib.py` | 66 | error branch with condition | i['query'] in qs |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/mask_kit/kitlib.py` | 68 | error branch with condition | list(a.shape) != list(c['hw']) or list(fr['size']) != list(c['hw'][::-1]) or len(i['box']) != 4 or (not np.isfinite(i['box']).all()) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/mask_kit/kitlib.py` | 77 | error branch with condition | not src or not any((n.casefold() in (q['question'] + ' ' + ' '.join(map(str, q.get('options') or []))).casefold() for q in src)) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/mask_kit/variantlib.py` | 2-8,19,21-22,24-25,27,29-30,32,34,36,38-39,43,45-49,55-57,59-67,69-75,77-79 | UNEXPLAINED | No test or rehearsal executed this job-source line. |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/mask_kit/variantlib.py` | 40 | error branch with condition | sm.get('schema') != 'mask-recall-variant-v1' or sm['experiment']['name'] != 'dense' |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/mask_kit/variantlib.py` | 41 | error branch with condition | complete['manifest_sha256'] != msha or binding.get('manifest_sha256') != msha or complete['captures'] != len(sm['captures']) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/mask_kit/variantlib.py` | 42 | error branch with condition | not binding.get('code_sha256') |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/mask_kit/variantlib.py` | 50 | error branch with condition | dense is None |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/mask_kit/variantlib.py` | 51 | error branch with condition | (dense['receipt_sha256'], dense['checkpoint_sha256']) != (base['receipt_sha256'], base['checkpoint_sha256']) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/mask_kit/variantlib.py` | 52 | error branch with condition | dense['baseline_cache_sha256'] != baseline_pins |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/mask_kit/variantlib.py` | 53 | error branch with condition | dense['contract'] != contract(SPECS['dense']) or set(dense['npz_sha256']) != {c['scene'] for c in base['captures']} |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/mask_kit/variantlib.py` | 54 | error branch with condition | dense['code_sha256'] != code_pins() |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/mask_kit/vendor/phrase.py` | 3,11-13 | UNEXPLAINED | No test or rehearsal executed this job-source line. |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 23-24,26,30-34,38,40,62,66-74,85-86,90-100,104-121,123-124,126,130,132-134,162-163,165-168,170,172,174,176,178,180-182,185,187,189-193,195-196,198,200-201,203,205-207,209-211,213-220,222-223,225,229-230,232,234-235,237-239,241-243,257-264,266-280,287,291,295,298,302-305,307-308,310-311,334,336-352,354-359,362,367-392,394-401,405,407,409-427,431-432,434-436,438-440,444-447,454,457,463,465-469,471-476,478-494,496-502,505-507,509-517,520-521,527-530,532,534-535,537,543-550,552-553,557,559-562,564,566,568-570,572,575-576,578-585,587,589-590,592-595,597-598,601-602,606-611,613-616,618,620-622,624-627,629,631,633-634,636-637,639,642-643,646,648,652-657,661 | UNEXPLAINED | No test or rehearsal executed this job-source line. |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 25 | error branch with condition | present and (not artifact.get('mdg') or not cfg.get('mdg')) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 39 | error branch with condition | family(typ) not in FAMILIES |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 61 | error branch with condition | len({t['id'] for t in tasks}) != len(tasks) or len({c['native'] for c in captures}) != len(captures) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 122 | error branch with condition | admitted and (not runtime) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 140 | error branch with condition | (r.get('schema'), r.get('arm'), r.get('scope')) != (SCHEMA, 'paired', 'r1') |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 143 | error branch with condition | (r.get('mask_source'), r.get('prompt_flag'), r.get('max_new_tokens'), r.get('thinking'), r.get('decoding'), r.get('layout')) != ('by_type', None, 16384, True, 'greedy', 'duplicate') |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 145 | error branch with condition | r.get('decode_budget') != Q.DECODE_BUDGET or r.get('candidate_universe_policy') != Q.UNIVERSE |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 147 | error branch with condition | r.get('geometry_refusal_policy') != GR.POLICY |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 149 | error branch with condition | r.get('fusion_policy') != FUSION or r['grounding'].get('allow_own_fallback') is not False or r['grounding'].get('depth_source') != 'tower_scaled' |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 151 | error branch with condition | not re.fullmatch('[0-9a-f]{64}', r['artifact']['sha256']) or r['artifact']['sha256'] == '0' * 64 |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 153 | error branch with condition | digest({k: v for k, v in r.items() if k != 'binding'}) != r['binding'] |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 155 | error branch with condition | r['adapter_sources'] != adapter_sources() or r['tree_sources'] != source_pins() |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 157 | error branch with condition | r.get('runtime_tree') != tree_identity(TREE, r['tree_sources']) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 164 | error branch with condition | r['candidate_policy'] != default_policy() |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 169 | error branch with condition | has_mdg(artifact, cfg) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 171 | error branch with condition | (cfg.get('frame_layout'), cfg.get('training_mode'), cfg.get('trace_program_version')) != ('duplicate', 'final', '3.14') |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 173 | error branch with condition | cfg.get('depth_enabled') is not True or cfg.get('depth_fov_source') != 'pose_head' |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 175 | error branch with condition | cfg.get('tool_mode_flag') or cfg.get('s1_route_policy', {}).get('name') != 'frozen-table-no-flag-v1' |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 177 | error branch with condition | artifact.get('step') != r['step'] or artifact.get('trace_program_version') != '3.14' |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 179 | error branch with condition | r['route_table'] != cfg['route_table'] |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 184 | error branch with condition | r.get('query_journal') != Q.journal_policy([dict(key='devrows:' + t['id'], family=family(t['question_type'])) for t in chosen]) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 186 | error branch with condition | r['keys'] != ['devrows:' + t['id'] for t in chosen] or not chosen |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 188 | error branch with condition | any((r['route_table'].get(t['question_type']) != 'route' for t in chosen)) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 194 | error branch with condition | r.get('geometry_refusals') != refused |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 197 | error branch with condition | r.get('mask_operand_refusals') != operand_refusals(served, refs, masks) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 199 | error branch with condition | r.get('candidate_universe_admission') != universe_admission(served, refs, masks) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 202 | error branch with condition | r['dry'] or r['parent_standin'] |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 204 | error branch with condition | not r.get('data_receipt') |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 208 | error branch with condition | g is None or masks is None |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 212 | error branch with condition | g.get('config') != r['config'] |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 224 | error branch with condition | r['perceptions'] != expected |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 231 | error branch with condition | args.arm != 'paired' or args.scope != 'r1' |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 233 | error branch with condition | args.parent_standin or args.step <= 0 or (not args.config) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 236 | error branch with condition | dest.exists() |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 240 | error branch with condition | has_mdg(load(checked(artifact)), cfg) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 335 | error branch with condition | not args.device.startswith('cuda:') |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 477 | error branch with condition | not parity['pass'] |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 503-504 | error branch with condition | not replay['byte_equal'] |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 508 | error branch with condition | not P.replay(script, geo, backend)['byte_equal'] |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 531 | error branch with condition | c.get('schema') != 'legs1-r1-complete-v1' or c.get('synthetic') is not False or c['request'] != pin(d / 'request.json') |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 533 | error branch with condition | c['items'] != len(request['keys']) or not load(checked(c['parity']))['pass'] |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 536 | error branch with condition | len(data) != 2 * len(request['keys']) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 558 | error branch with condition | bundle.get('synthetic') is not False |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 563 | error branch with condition | (c.get('schema'), c.get('synthetic'), c['request']) != ('legs1-r1-complete-v1', False, req_pin) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 565 | error branch with condition | (r['step'], r['artifact']['sha256']) != (step, artifact_sha256) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 567 | error branch with condition | not load(checked(c['parity']))['pass'] or c['items'] != len(r['keys']) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 571 | error branch with condition | len(native) != 2 * len(r['keys']) or bundle['arms'] != arms |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 574 | error branch with condition | (bundle['expected_keys'], bundle['binding'], bundle['artifact_sha256'], bundle['adapter_sources']) != (r['keys'], r['binding'], r['artifact']['sha256'], r['adapter_sources']) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 577 | error branch with condition | bundle['perception_by_key'] != expected |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 586 | error branch with condition | pair != geometry_refusal_pair(task, r) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 588 | error branch with condition | any((row.get('geometry_refusal') for row in pair)) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 591 | error branch with condition | bundle.get('geometry_scores') != geometry_scores or bundle.get('geometry_refusal_policy') != GR.POLICY |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 596 | error branch with condition | bundle.get('reader_semantics') != Q.REPORT_SEMANTICS |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 600 | error branch with condition | any((bundle.get(name) != report[name] for name in ('report_scope', 'training_decision_allowed', 'perception_disclosure'))) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 612 | error branch with condition | items['sha256'] != m['items_sha256'] |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 617 | error branch with condition | d['experiment']['name'] != 'dense' or (d['checkpoint_sha256'], d['receipt_sha256']) != (m['checkpoint_sha256'], m['receipt_sha256']) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 619 | error branch with condition | m['experiment'].get('dense_source') is not None and variants.dense_source(dense) != m['experiment']['dense_source'] |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 623 | error branch with condition | sam['sha256'] != m['receipt_sha256'] |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 630 | error branch with condition | {k: v for k, v in dc[native].items() if k != 'cache_contract'} != {k: v for k, v in c.items() if k != 'cache_contract'} |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 635 | error branch with condition | raw.get('receipt') != load(sam['path']) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 638 | error branch with condition | not j or j[-1].get('event') != 'complete' or j[-1].get('sha256') != value['sha256'] |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 641 | error branch with condition | not any((e.get('event') == 'reuse_dense' and e.get('sha256') == entry['dense_cache']['sha256'] for e in rows(entry['journal']['path']))) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/nomdg.py` | 647 | error branch with condition | local(args.output).exists() |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 22-24,28-29,31,33,36-40,43,45,47,52-53,57-58,62-64,70-72,74,76,78-79,81-82,84,86-87,89-90,93-96,99,102-106,108-111,113-114,116,118-119,121,123-124,126-133,136-137,155-159,162,164-167,183-185,196-200,203,205-207,209-211,213-214,255,285-293,295-296,299-300,302-304,306-307,309-310,312-313,317,322,326,328-330,334,338,341,346,348-349,351-353,358-361,364 | UNEXPLAINED | No test or rehearsal executed this job-source line. |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 30 | error branch with condition | manifest.get('density') != SETTING or manifest.get('checkpoint_sha256') != SAM_SHA |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 32 | error branch with condition | manifest.get('experiment', {}).get('name') != 'dense_aliases' |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 35 | error branch with condition | any((x.get('manifest_sha256') != manifest_sha or x.get('stub') is not False for x in (binding, complete))) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 41 | error branch with condition | complete.get('captures') != len(manifest['captures']) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 44 | error branch with condition | manifest.get('schema') != 'mask-recall-variant-v1' or len(manifest['captures']) != 152 |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 46 | error branch with condition | any((c.get('cache_contract') != SETTING for c in manifest['captures'])) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 65 | error branch with condition | missing |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 73 | error branch with condition | r.get('schema') != 'legs1-frozen-mask-cache-v1' or r.get('setting') != SETTING |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 75 | error branch with condition | r.get('frozen_kit') != frozen_kit.identity() |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 77 | error branch with condition | r.get('producer_sha256') != sha(Path(__file__).with_name('nomdg.py')) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 83 | error branch with condition | len(self.captures) != len(self.manifest['captures']) or set(r['captures']) != set(self.captures) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 85 | error branch with condition | r['items']['sha256'] != self.manifest.get('items_sha256') |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 88 | error branch with condition | sha(checked(r['sam_receipt'])) != self.manifest['receipt_sha256'] |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 92 | error branch with condition | (self.dense_manifest['experiment']['name'], self.dense_manifest['checkpoint_sha256'], self.dense_manifest['receipt_sha256']) != ('dense', SAM_SHA, self.manifest['receipt_sha256']) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 107 | error branch with condition | c['anchor_indices'] != list(batch['frame_indices']) or [f['sha256'] for f in c['frames']] != [f['sha256'] for f in si['frames']] |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 115 | error branch with condition | not journal or journal[-1].get('event') != 'complete' or journal[-1].get('sha256') != entry['cache']['sha256'] |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 120 | error branch with condition | not dj or dj[-1].get('event') != 'complete' or dj[-1].get('sha256') != entry['dense_cache']['sha256'] |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 122 | error branch with condition | not any((e.get('event') == 'reuse_dense' and e.get('sha256') == entry['dense_cache']['sha256'] for e in journal)) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 125 | error branch with condition | raw.get('receipt') != receipt or dense.get('receipt') != receipt |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 150 | error branch with condition | geometry.contract.profile != 'scaled_g3t_depth' or geometry.depth_scale_count != 1 |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 163 | error branch with condition | value.geometry_error |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 204 | error branch with condition | ground_backend is None |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 212 | error branch with condition | applied.get(obj['instance_id']) is not True |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 229-230,232,234-236,238-239,241-244,248 | GPU decode | checkpoint restoration or sampled GPU logits |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 231 | error branch with condition | getattr(model, 'trace_program_version', None) != '3.14' |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 233 | error branch with condition | hasattr(getattr(model, 'auxiliary_heads', None), 'mdg') or getattr(model, 'mdg_head', None) is not None |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 237 | error branch with condition | MAX_CALL_TOKENS != Q.DECODE_BUDGET['call_window_tokens'] |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 240 | error branch with condition | tokens is None |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 294 | error branch with condition | not match |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 298 | error branch with condition | not re.search('(?<!\\w)' + re.escape(name) + '(?!\\w)', task['question'] + ' ' + ' '.join(task.get('options') or []), re.I) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 301 | error branch with condition | len(names) != 2 or len(set(names)) != 2 |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 305 | error branch with condition | ref['segments'][-1]['call'] not in (old, new) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 308 | error branch with condition | typ not in ('camera_displacement', 'camera_movement_direction', 'camera_rotation') |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 311 | error branch with condition | not match or any((not 1 <= int(n) <= 32 for n in match.groups())) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/perception.py` | 350 | error branch with condition | not units |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/r1.py` | 16-17,19-20,22,24-26,30,32-36,38,40-43,45,47-49,51-52,54,57,59,61,64,66-67,69,71,73,78,80-85,87-93,95-96,98-106,108-113,117-118,120-124,126-128,150,159-162,166,168-170 | UNEXPLAINED | No test or rehearsal executed this job-source line. |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/r1.py` | 18 | error branch with condition | not isinstance(calls, list) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/r1.py` | 21 | error branch with condition | type(errors) is not int or errors < 0 |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/r1.py` | 31 | error branch with condition | bundle.get('schema') != 'legs1-r1-nomdg-v1' or set(bundle.get('arms', {})) != {'unflagged', 'scripted'} |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/r1.py` | 37 | error branch with condition | row['key'] in idx |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/r1.py` | 39 | error branch with condition | row.get('arm') != arm |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/r1.py` | 44 | error branch with condition | not keys or keys != set(arms['scripted']) or keys != set(bundle['expected_keys']) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/r1.py` | 50 | error branch with condition | any((a.get(k) != b.get(k) for k in identity)) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/r1.py` | 53 | error branch with condition | family(row['question_type']) not in FAMILIES |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/r1.py` | 56 | error branch with condition | not row.get('perception_identity') or row.get('mask_source') != ('svp_sam3' if family(row['question_type']) == 'object_abs_distance' else None) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/r1.py` | 58 | error branch with condition | row['perception_identity'] != bundle['perception_by_key'][key] |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/r1.py` | 60 | error branch with condition | row['checkpoint_sha256'] != bundle['artifact_sha256'] or row['binding'] != bundle['binding'] |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/r1.py` | 63 | error branch with condition | type(row.get('called')) is not bool or any((type(row.get(k)) is not int or row[k] < 0 for k in ('call_errors', 'version_errors'))) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/r1.py` | 65 | error branch with condition | type(row.get('no_answer')) is not bool |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/r1.py` | 68 | error branch with condition | value is not None and (type(value) not in (int, float) or not math.isfinite(value) or (not 0 <= value <= 1)) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/r1.py` | 70 | error branch with condition | 'decode' in row and any((row[k] != v for k, v in accounting(row['decode']).items())) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/r1.py` | 72 | error branch with condition | row['no_answer'] and any((v not in (None, 0.0) for v in row['scores'].values())) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/r1.py` | 77 | error branch with condition | row.get('geometry_refusal') and (row.get('decode_executed') is not False or 'decode' in row or row['called'] or row['call_errors'] or row['version_errors'] or (not row['no_answer'])) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/r1.py` | 79 | error branch with condition | row['arm'] == 'scripted' and 'decode' in row and (row['no_answer'] != row['decode'].get('strict_no_answer')) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/r1.py` | 94 | error branch with condition | len(labels) != 1 |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/r1.py` | 97 | error branch with condition | any((r['scores'].get(label) is None for rows in rs.values() for r in rows)) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/read_runtime.py` | 1-2,4,7,12-14,16,19-27,30,35-39,43,45,47,50,52,54,56,58-59,61-67,71 | UNEXPLAINED | No test or rehearsal executed this job-source line. |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/read_runtime.py` | 15 | error branch with condition | path.suffix != '.json' or path.stat().st_size > 16 * 1024 ** 2 |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/read_runtime.py` | 29 | error branch with condition | any((name in data and type(data[name]) is not bool for name in ('production_authorized', 'gpu_first_step_pending'))) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/read_runtime.py` | 34 | error branch with condition | data.get('schema') != 's1-in-job-data-v1' or data.get('status') != 'PREPARED' or data.get('synthetic', False) is not False or (data.get('rehearsal') is not False) or (data.get('real_frames_verified') is not True) or (data.get('config') != config_pin) or (data.get('preparation') != cfg.get('preparation')) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/read_runtime.py` | 42 | error branch with condition | receipt.get('schema') != 'c1-preparation-v1' or receipt.get('config_sha256') != identity or artifact.get('config_sha256') != identity or (receipt.get('trainer_commit') != commit) or (artifact.get('base_identity') != cfg['base_identity']) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/read_runtime.py` | 44 | error branch with condition | set(cfg.get('streams', {})) != {'pose', 'pointing', 'routing', 'vqa'} |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/read_runtime.py` | 46 | error branch with condition | any(('mdg' in value or 'geometry_online' in value for value in (cfg, receipt, artifact))) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/read_runtime.py` | 49 | error branch with condition | (cfg.get('training_mode'), cfg.get('frame_layout'), cfg.get('trace_program_version'), cfg.get('depth_enabled'), cfg.get('depth_fov_source')) != ('final', 'duplicate', '3.14', True, 'pose_head') |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/read_runtime.py` | 51 | error branch with condition | {name: value['receipt'] for name, value in receipt['streams'].items()} != cfg['streams'] |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/read_runtime.py` | 53 | error branch with condition | any((receipt.get(name) != cfg.get(name) for name in FIELDS)) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/read_runtime.py` | 55 | error branch with condition | trainer.data.layout_settings(receipt) != trainer.data.layout_settings(cfg) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/read_runtime.py` | 57 | error branch with condition | receipt.get('s1_route_policy') != route_policy(cfg) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/read_runtime.py` | 60 | error branch with condition | receipt.get(name) != cfg.get(name) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/read_runtime.py` | 74-79,81-88,90,92-93,100 | GPU decode | checkpoint restoration or sampled GPU logits |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/read_runtime.py` | 80 | error branch with condition | torch.device(device).type != 'cuda' |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/read_runtime.py` | 89 | error branch with condition | artifact['base_identity'] != cfg['base_identity'] or artifact['config_sha256'] != trainer.identity(cfg) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/read_runtime.py` | 91 | error branch with condition | not hasattr(processor, '_routing_tokens') or model.trace_program_version != '3.14' |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/reader_policy.py` | 26 | error branch with condition | policy != DECODE_BUDGET |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/reader_policy.py` | 34 | error branch with condition | len(closing) != 1 or not self.close_ids or closing[0] not in self.close_ids or (type(self.eos) is not int) or (self.eos < 0) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/reader_policy.py` | 63-66,77,79-80,82,100-101,111-113,158,163-171,176-183,185-186,188-191,195-198,200-204,209,212-216,220,226-233,235-237,241,246-252,254,256-257,259-260,263,265,267-268 | UNEXPLAINED | No test or rehearsal executed this job-source line. |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/reader_policy.py` | 71 | error branch with condition | ids |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/reader_policy.py` | 73 | error branch with condition | len(ids) <= self.previous_position |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/reader_policy.py` | 123 | error branch with condition | type(total_tokens) is not int or total_tokens < self.callbacks |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/reader_policy.py` | 184 | error branch with condition | not isinstance(queries, list) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/reader_policy.py` | 199 | error branch with condition | item['key'] in keys |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/reader_policy.py` | 234 | error branch with condition | row['arm'] in pair |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/reader_policy.py` | 240 | error branch with condition | set(pair) != {'unflagged', 'scripted'} or pair['unflagged']['question_unit'] != pair['scripted']['question_unit'] or bool(pair['unflagged'].get('geometry_refusal')) != bool(pair['scripted'].get('geometry_refusal')) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/reader_policy.py` | 255 | error branch with condition | any((value is None for value in values)) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/routed.py` | 33-35,45,47,49,51-52,56-58,61-62,64,66-68,72-73,75,84-88,90-92,94-97,100,104-107,109-117,120-127,130-141,144-145,147-159,161-162,164,167-170,177-180,182-183,187-188,190-191,194-199,201,205-206,208,211-225 | UNEXPLAINED | No test or rehearsal executed this job-source line. |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/routed.py` | 36 | error branch with condition | r.get('schema') != 'legs1-routed-read-v1' or r.get('arm') not in ARMS |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/routed.py` | 37 | error branch with condition | r.get('scope') not in ('supported600', 'main1525') |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/routed.py` | 38 | error branch with condition | r['max_new_tokens'] != 16384 or r['thinking'] is not True or r['decoding'] != 'greedy' or (r['layout'] != 'duplicate') |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/routed.py` | 39 | error branch with condition | r['prompt_flag'] != FLAGS[r['arm']] |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/routed.py` | 40 | error branch with condition | r['mask_source'] != 'mdg' |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/routed.py` | 41 | error branch with condition | r['grounding'].get('allow_own_fallback') is not False or r['grounding'].get('depth_source') != 'tower_scaled' |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/routed.py` | 42 | error branch with condition | r['fusion_policy'] != 'fit_gbox_policy_voteb5_best1_v1' |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/routed.py` | 43 | error branch with condition | r['artifact']['sha256'] == '0' * 64 or not re.fullmatch('[0-9a-f]{64}', r['artifact']['sha256']) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/routed.py` | 44 | error branch with condition | digest({k: v for k, v in r.items() if k != 'binding'}) != r['binding'] |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/routed.py` | 46 | error branch with condition | sha(__file__) != r['driver_sha256'] or source_pins() != r['tree_sources'] |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/routed.py` | 48 | error branch with condition | r.get('runtime_tree') != tree_identity(TREE, r['tree_sources']) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/routed.py` | 50 | error branch with condition | r['dry'] or r['parent_standin'] |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/routed.py` | 53 | error branch with condition | cfg.get('frame_layout') != 'duplicate' or cfg.get('training_mode') != 'final' or cfg.get('trace_program_version') != '3.14' |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/routed.py` | 54 | error branch with condition | not cfg.get('geometry_online') or not cfg.get('mdg') |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/routed.py` | 55 | error branch with condition | load(r['artifact']['path']).get('step') != r['step'] |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/routed.py` | 63 | error branch with condition | getattr(args, 'camera_cohort', None) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/routed.py` | 65 | error branch with condition | dest.exists() |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/routed.py` | 69 | error branch with condition | args.arm == 'scripted' and any(('devrows:' + t['id'] not in refs for t in chosen)) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/routed.py` | 70 | error branch with condition | args.step <= 0 |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/routed.py` | 71 | error branch with condition | args.parent_standin and (not args.dry or args.sha256 != PARENT_SHA) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/routed.py` | 74 | error branch with condition | not args.dry and (config is None or geometry is None) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/routed.py` | 89 | error branch with condition | manifest.get('schema') != 's1-predicted-geometry-v1' |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/routed.py` | 93 | error branch with condition | clip not in manifest['videos'] |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/routed.py` | 108 | error branch with condition | not args.device.startswith('cuda:') |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/routed.py` | 119 | error branch with condition | model.trace_program_version != '3.14' |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/routed.py` | 146 | error branch with condition | not parity['pass'] |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/routed.py` | 160 | error branch with condition | not replayed['byte_equal'] |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/routed.py` | 165-166 | error branch with condition | request['arm'] == 'forced_direct' and called |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/routed.py` | 200 | error branch with condition | r['arm'] != name |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/routed.py` | 202 | error branch with condition | not load(checked(c['parity']))['pass'] |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/routed.py` | 203 | error branch with condition | len(data) != len(r['keys']) or {x['key'] for x in data} != set(r['keys']) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/routed.py` | 204 | error branch with condition | any((x['binding'] != r['binding'] for x in data)) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/routed.py` | 207 | error branch with condition | a['key'] != b['key'] or a['prefill_identity'] != b['prefill_identity'] |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/runtime_tree.py` | 17 | error branch with condition | recorded.get('schema') != 'legs1-runtime-tree-v1' or recorded.get('sources_sha256') != EXPECTED_SOURCES_SHA or digest(recorded['sources']) != EXPECTED_SOURCES_SHA or (recorded['files'] != len(recorded['sources'])) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/runtime_tree.py` | 22 | error branch with condition | not local(path).is_relative_to(root) |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/runtime_tree.py` | 25,27 | error branch with condition | actual != recorded['sources'] |
| `code/sj/orch_cd/evalx/work/milestone/native/out2/runtime_tree.py` | 34 | error branch with condition | value != EXPECTED_SOURCES_SHA |
| `code/sj/orch_cd/evalx/work/milestone/native_bootstrap.py` | 21-22,24-26,28,32,34,37,39-40,42,44,46-49,51-52,54-60,62-63,65,67,69,73-84,86-87,89-90,94 | UNEXPLAINED | No test or rehearsal executed this job-source line. |
| `code/sj/orch_cd/evalx/work/milestone/native_bootstrap.py` | 23 | error branch with condition | not path.is_absolute() or not path.is_file() |
| `code/sj/orch_cd/evalx/work/milestone/native_bootstrap.py` | 27 | error branch with condition | actual != pin['sha256'] |
| `code/sj/orch_cd/evalx/work/milestone/native_bootstrap.py` | 33 | error branch with condition | not sys.flags.isolated or not sys.dont_write_bytecode or os.environ.get('PYTHONPATH') |
| `code/sj/orch_cd/evalx/work/milestone/native_bootstrap.py` | 36 | error branch with condition | spec.get('schema') != SCHEMA or spec.get('runtime_archive_sha256') != ARCHIVE or spec.get('source_map_sha256') != SOURCE |
| `code/sj/orch_cd/evalx/work/milestone/native_bootstrap.py` | 38 | error branch with condition | checked(spec['python']).resolve() != Path(sys.executable).resolve() |
| `code/sj/orch_cd/evalx/work/milestone/native_bootstrap.py` | 41 | error branch with condition | any((not p.is_absolute() or not p.is_dir() for p in paths)) or len(set(paths)) != len(paths) |
| `code/sj/orch_cd/evalx/work/milestone/native_bootstrap.py` | 43 | error branch with condition | set(spec['imports']) != set(IMPORTS) |
| `code/sj/orch_cd/evalx/work/milestone/native_bootstrap.py` | 45 | error branch with condition | any((name in sys.modules for name in IMPORTS)) |
| `code/sj/orch_cd/evalx/work/milestone/native_bootstrap.py` | 50 | error branch with condition | checked(spec['sitecustomize']).resolve() != site.resolve() |
| `code/sj/orch_cd/evalx/work/milestone/native_bootstrap.py` | 53 | error branch with condition | spec.get('sitecustomize') is not None |
| `code/sj/orch_cd/evalx/work/milestone/native_bootstrap.py` | 61 | error branch with condition | not expected.resolve().is_relative_to(root) |
| `code/sj/orch_cd/evalx/work/milestone/native_bootstrap.py` | 64 | error branch with condition | Path(value.__file__).resolve() != expected.resolve() |
| `code/sj/orch_cd/evalx/work/milestone/native_bootstrap.py` | 66 | error branch with condition | name in REQUIRED_VERSIONS and getattr(value, '__version__', None) != REQUIRED_VERSIONS[name] |
| `code/sj/orch_cd/evalx/work/milestone/native_bootstrap.py` | 85 | error branch with condition | not command |
| `code/sj/orch_cd/evalx/work/milestone/native_bootstrap.py` | 88 | error branch with condition | target.name not in spec['entrypoints'] or checked(spec['entrypoints'][target.name]).resolve() != target.resolve() |
| `code/sj/orch_cd/evalx/work/milestone/orchard_job.py` | 25-26,28-31,36-37,41-49,51,55-66,69-75,77-78,81-83,86-87,91,94,97,100-103,105-106,108,111,119-127,133,137-140,151-157,161-165,167-168,170-181,183-184,189-190,192-193,195,197-203,205-225,227-240,244-249,251-253,257-258,260,262-264,266-267,271 | Orchard-only staging | inherited allocation or return transport |
| `code/sj/orch_cd/evalx/work/milestone/orchard_job.py` | 27 | error branch with condition | not path.is_absolute() or '..' in path.parts |
| `code/sj/orch_cd/evalx/work/milestone/orchard_job.py` | 76 | error branch with condition | len(matches) != 1 |
| `code/sj/orch_cd/evalx/work/milestone/orchard_job.py` | 80 | error branch with condition | value['filesystem'] not in ('ext4', 'xfs', 'btrfs', 'tmpfs') or (value['filesystem'] != 'tmpfs' and (not value['source'].startswith('/dev/'))) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_job.py` | 85 | error branch with condition | not str(job).isdigit() or value['mount'] != '/tmp' or 'job_tmp' not in parts or (str(job) not in parts) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_job.py` | 104 | error branch with condition | len(assigned) != 1 or assigned[0][2] != 'NVIDIA H100 80GB HBM3' |
| `code/sj/orch_cd/evalx/work/milestone/orchard_job.py` | 107 | error branch with condition | not visible or ',' in visible or (visible.startswith('GPU-') and visible != selected[1]) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_job.py` | 110 | error branch with condition | require_empty and (float(selected[3]) > 32 or float(selected[4]) != 0 or selected[1] in processes.stdout) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_job.py` | 182 | error branch with condition | proof['source'] != evidence['storage']['source'] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_job.py` | 194 | error branch with condition | code |
| `code/sj/orch_cd/evalx/work/milestone/orchard_job.py` | 196 | error branch with condition | not (source / 'COMPLETE.json').is_file() or (source / 'FAILED.json').exists() |
| `code/sj/orch_cd/evalx/work/milestone/orchard_job.py` | 250 | error branch with condition | config.get('schema') != 'evalx-orchard-batch-v1' |
| `code/sj/orch_cd/evalx/work/milestone/orchard_job.py` | 256 | error branch with condition | S.sha(Path(args.config).parent / 'REVIEW.json') != config['launcher_review_pin']['sha256'] or review.get('verdict') != 'ACCEPT' or (not review.get('reviewer')) or (review.get('code_pins_sha256') != digest) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_job.py` | 259 | error branch with condition | S.sha(Path(args.config).parent / Path(path).name) != expected |
| `code/sj/orch_cd/evalx/work/milestone/orchard_job.py` | 261 | error branch with condition | review.get('synthetic') is True |
| `code/sj/orch_cd/evalx/work/milestone/orchard_job.py` | 265 | error branch with condition | S.sha(payload) != config['payload_sha256'] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_launcher.py` | 29,33,37,39,43-50,54-56,58,91-92,99,111,115-116,118-119,121-125,128-131,133,135-136,138,144-146,148-150,155-160,163-165,167,169-174,176-180,182-185,187-190,195-196,199-200,202,206-210,212-217,221,223-225,236-239,245,248-251,255-256,258-260,262-263,265-267,269-277,279-280,286-298,302-303,305,307,311,315-320,324,326-328,330-331,333-334,337-339,341-342,345-350,353-355,357,361-365,369-381,383-385,387,391 | Orchard-only staging | inherited allocation or return transport |
| `code/sj/orch_cd/evalx/work/milestone/orchard_launcher.py` | 38 | error branch with condition | not re.fullmatch('[a-z][0-9a-f]{8,32}', token) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_launcher.py` | 57 | error branch with condition | len(encoded) > 3 * 1024 ** 2 |
| `code/sj/orch_cd/evalx/work/milestone/orchard_launcher.py` | 117 | error branch with condition | not match |
| `code/sj/orch_cd/evalx/work/milestone/orchard_launcher.py` | 120 | error branch with condition | script != render_batch(bundle, config['token']) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_launcher.py` | 127 | error branch with condition | not entry.isfile() or entry.name in files or entry.size < 0 or (len(files) > 32) or (total > 32 * 1024 ** 2) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_launcher.py` | 132 | error branch with condition | set(files) != expected or json.loads(files['bootstrap/CONFIG.json']) != config |
| `code/sj/orch_cd/evalx/work/milestone/orchard_launcher.py` | 134 | error branch with condition | json.loads(files['bootstrap/ORCHARD_ASSETS.json']) != config['assets'] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_launcher.py` | 137 | error branch with condition | hashlib.sha256(files['bootstrap/' + Path(path).name]).hexdigest() != digest |
| `code/sj/orch_cd/evalx/work/milestone/orchard_launcher.py` | 140 | error branch with condition | hashlib.sha256(files['bootstrap/REVIEW.json']).hexdigest() != config['launcher_review_pin']['sha256'] or hashlib.sha256(files['bootstrap/payload.tar.gz']).hexdigest() != config['payload_sha256'] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_launcher.py` | 147 | error branch with condition | config.get('schema') != 'evalx-orchard-batch-v1' |
| `code/sj/orch_cd/evalx/work/milestone/orchard_launcher.py` | 151 | error branch with condition | plan['plan_sha256'] != config['plan_sha256'] or config['spec']['scope'] != 'direct' |
| `code/sj/orch_cd/evalx/work/milestone/orchard_launcher.py` | 162 | error branch with condition | not entry.isfile() or entry.name in files or entry.size < 0 or (len(files) >= 256) or (total > 32 * 1024 ** 2) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_launcher.py` | 175 | error branch with condition | config['stage']['vnice']['sha256'] != config['assets']['vnice_sha256'] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_launcher.py` | 181 | error branch with condition | hashlib.sha256(files.get(name, b'')).hexdigest() != digest |
| `code/sj/orch_cd/evalx/work/milestone/orchard_launcher.py` | 186 | error branch with condition | json.loads(files[path]) != config[field] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_launcher.py` | 191 | error branch with condition | files.get(wrapper) != command.encode() or set(files) != expected |
| `code/sj/orch_cd/evalx/work/milestone/orchard_launcher.py` | 198 | error branch with condition | value.get('verdict') != 'ACCEPT' or not value.get('reviewer') or value.get('synthetic') is True or (value.get('code_pins_sha256') != canonical(pins)) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_launcher.py` | 201 | error branch with condition | S.sha(name) != expected |
| `code/sj/orch_cd/evalx/work/milestone/orchard_launcher.py` | 211 | error branch with condition | destination.exists() |
| `code/sj/orch_cd/evalx/work/milestone/orchard_launcher.py` | 220 | error branch with condition | S.sha(artifact) != wrapper['artifact_sha256'] or type(artifact_value.get('step')) is not int or artifact_value['step'] != step or (artifact_value['training_source_seal']['tree_sha256'] != C.SOURCE) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_launcher.py` | 261 | error branch with condition | path.stat().st_size > 8 * 1024 ** 2 or path.is_symlink() |
| `code/sj/orch_cd/evalx/work/milestone/orchard_launcher.py` | 304 | error branch with condition | any((len(row) != 5 for row in rows)) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_launcher.py` | 306 | error branch with condition | any((row[2] == user and 'gpu' in row[4].lower() for row in rows)) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_launcher.py` | 323 | error branch with condition | S.sha(destination / 'BATCH.sh') != batch_pin['sha256'] or S.sha(destination / 'CONFIG.json') != batch_pin['config_sha256'] or config['launcher_pins'] != {str(ROOT / name): S.sha(ROOT / name) for name in CORE} |
| `code/sj/orch_cd/evalx/work/milestone/orchard_launcher.py` | 325 | error branch with condition | S.sha(config['launcher_review_pin']['path']) != config['launcher_review_pin']['sha256'] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_launcher.py` | 329 | error branch with condition | (destination / 'SUBMIT_INTENT.json').exists() |
| `code/sj/orch_cd/evalx/work/milestone/orchard_launcher.py` | 332 | error branch with condition | queue.returncode |
| `code/sj/orch_cd/evalx/work/milestone/orchard_launcher.py` | 340 | error branch with condition | not NOTICES.parent.is_dir() |
| `code/sj/orch_cd/evalx/work/milestone/orchard_launcher.py` | 356 | error branch with condition | value['status'] != 'SUBMITTED' |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/FRAME_PULLER.py` | 11-17,20-66,69-70 | Orchard-only staging | inherited allocation or return transport |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/kernels.py` | 14-15,19,21-22,24-27,29,31,35,37-39,41-45,47-48,50,52-61,63,94,100,107,109,126,128,130,134-136,141-142,144,148-152,156-158,160,162-164,167-168,171-172,180-182,185-187,189-190,192,196,198-201,203-204,206-207,211-214 | Orchard-only staging | inherited allocation or return transport |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/kernels.py` | 18 | error branch with condition | not tasks or not families or len(set(families)) != len(families) or (type(max_captures) is not int) or (max_captures < 1) or (type(per_family) is not int) or (per_family < 1) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/kernels.py` | 20 | error branch with condition | len({t['key'] for t in tasks}) != len(tasks) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/kernels.py` | 23 | error branch with condition | not isinstance(item_keys, list) or len(item_keys) != 10 or len(set(item_keys)) != 10 |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/kernels.py` | 30 | error branch with condition | distance_datasets != Counter(DISTANCE_DATASETS) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/kernels.py` | 34 | error branch with condition | [task['key'] for task in selected] != item_keys or item_keys[0] != tasks[0]['key'] or counts != Counter(PILOT_COUNTS) or (set(families) != set(PILOT_COUNTS)) or (len(captures) > max_captures) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/kernels.py` | 40 | error branch with condition | task['family'] not in families |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/kernels.py` | 46 | error branch with condition | len(chosen) >= max_captures |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/kernels.py` | 51 | error branch with condition | not candidates or max(map(gain, candidates)) == 0 |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/kernels.py` | 62 | error branch with condition | selected[0]['key'] != tasks[0]['key'] or any((counts[f] != per_family for f in families)) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/kernels.py` | 74 | error branch with condition | len(tasks) != 636 or len({row['key'] for row in tasks}) != 636 or len(names) != 84 or (len(set(names)) != 84) or (set(names) != {row['native'] for row in tasks}) or any((row.get('status') not in ('PASS', 'REFUSED') for row in geometry)) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/kernels.py` | 80 | error branch with condition | not isinstance(preferred, list) or len(preferred) != 10 or len(set(preferred)) != 10 or (not set(preferred) <= {row['key'] for row in tasks}) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/kernels.py` | 114 | error branch with condition | len(selected) != 10 or Counter((row['family'] for row in selected)) != Counter(PILOT_COUNTS) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/kernels.py` | 129 | error branch with condition | len(matches) != 1 or matches[0].decorator_list |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/kernels.py` | 143 | error branch with condition | len(matches) != 1 |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/kernels.py` | 161 | error branch with condition | len(counts) != 1 or counts[0] <= restore_at or counts[0] + 1 >= len(run.body) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/kernels.py` | 166 | error branch with condition | not isinstance(loop, ast.For) or ast.unparse(loop.target) != 'key' or ast.unparse(loop.iter) != "request['keys']" |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/kernels.py` | 170 | error branch with condition | not any((isinstance(n, ast.Constant) and n.value == 'GPU_PARITY.json' for statement in prefix for n in ast.walk(statement))) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/kernels.py` | 188 | error branch with condition | len(captures) != 1 |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/kernels.py` | 197 | error branch with condition | set(paths) != {'nomdg', 'geometry'} or set(pins) != set(paths) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/kernels.py` | 202 | error branch with condition | not path.is_absolute() or path.is_symlink() |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/kernels.py` | 205 | error branch with condition | hashlib.sha256(data).hexdigest() != pins[name] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_common.py` | 21-25,29-30,34-35,37-38,41,67,71,73,77,82-83,85,92,96-97,101,103-104,106,111-114,117-119,123,136-144 | Orchard-only staging | inherited allocation or return transport |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_common.py` | 36 | error branch with condition | not path.is_absolute() or '..' in path.parts |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_common.py` | 40 | error branch with condition | path.is_symlink() or not path.is_file() or sha(path) != record['sha256'] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_common.py` | 47 | error branch with condition | path.stat().st_size > 16 * 1024 ** 2 |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_common.py` | 78 | error branch with condition | text.splitlines().count(order_line(config)) != 1 |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_common.py` | 84 | error branch with condition | config.get('build_only') is not False |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_common.py` | 91 | error branch with condition | family.get('schema') != 'evalx-orchard-native-family-v1' or family.get('synthetic') is not False or family.get('modes') != ['pilot', 'full'] or (family.get('partitions') != ['general', 'advanced']) or (config['assets'] != family['assets']) or (config['limits'] != family['limits'][config['mode']]) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_common.py` | 95 | error branch with condition | review.get('verdict') != 'ACCEPT' or not review.get('reviewer') or review.get('synthetic') is not False or (review.get('family_sha256') != config['family']['sha256']) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_common.py` | 102 | error branch with condition | any((authority.get(key) != value for key, value in expected.items())) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_common.py` | 105 | error branch with condition | set(contract) != WORKER_FIELDS or any((config['worker'].get(k) != v for k, v in contract.items())) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_common.py` | 110 | error branch with condition | config['logical_run'] != str(LOGICAL_ROOT / 'runs' / config['token']) or config.get('plan_sha256') != plan(config) or config['transport'].get('artifact_sha256') != config['worker']['artifact']['sha256'] or (config['transport'].get('step') != config['step']) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_common.py` | 116 | error branch with condition | projection.get('projection_scenario') not in M.SCENARIOS or authority.get('projection_scenario') != projection['projection_scenario'] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_common.py` | 122 | error branch with condition | report['registered_selection'] != config['worker']['pilot_selection'] or sorted((row['native'] for row in report['geometry'])) != config['worker']['geometry_captures'] or [row['key'] for row in report['full_item_candidates']] != config['worker']['expected_keys'] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_common.py` | 132 | error branch with condition | config.get('schema') != SCHEMA or config.get('synthetic') is not False or config.get('mode') not in ('pilot', 'full') or (config.get('partition') not in ('general', 'advanced')) or (type(config.get('step')) is not int) or (config['step'] < 1) or (not re.fullmatch('[a-z][0-9a-f]{8,32}', config.get('token', ''))) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_common.py` | 134 | error branch with condition | config.get('gpus') != 1 or type(config['gpus']) is not int |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_common.py` | 145 | error branch with condition | artifact.get('step') != config['step'] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_cpu_replica.py` | 1-45,47-121,123-124,126,128-131,135-139 | Orchard-only staging | inherited allocation or return transport |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_cpu_replica.py` | 125 | error branch with condition | failed |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_cpu_replica.py` | 127 | error branch with condition | res['operand_refusals'] or not obj or (not all((row[1] for row in res['mask cache entries for distance items']))) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_job.py` | 24-35,39,42,45,49-52,54-55,57,60,68-69,73,75,79-85,87-92,96-97,99-103,107-108,111,115-123,125,127,129,133-137,149,151,153-155,157-160,164-165,169,171-172,175,179-182,184-185,187-209,211-214,219-220,222-226,231-237,239-260,262-266,270-276,280 | Orchard-only staging | inherited allocation or return transport |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_job.py` | 53 | error branch with condition | len(assigned) != 1 or assigned[0][2] != 'NVIDIA H100 80GB HBM3' |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_job.py` | 56 | error branch with condition | not visible or ',' in visible or (visible.startswith('GPU-') and visible != selected[1]) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_job.py` | 59 | error branch with condition | require_empty and (float(selected[3]) > 32 or float(selected[4]) != 0 or selected[1] in processes.stdout) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_job.py` | 72 | error branch with condition | not job.isdigit() or not os.uname().nodename.startswith('orchard-') or os.environ.get('SLURM_JOB_PARTITION') != config['partition'] or (Path(root).resolve() != Path('/tmp') / ('evalx_native_' + job + '_' + config['token'])) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_job.py` | 74 | error branch with condition | pwd.getpwuid(os.getuid()).pw_name != 'jjyeung' |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_job.py` | 124 | error branch with condition | now - last_change > limits['stall_seconds'] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_job.py` | 126 | error branch with condition | now - started > limits['gpu_seconds'] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_job.py` | 128 | error branch with condition | process.returncode |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_job.py` | 148 | error branch with condition | report.get('synthetic') is not False or report.get('training_decision_allowed') is not False or report.get('full_read_authorized') is not False or (report.get('family_sha256') != config['family']['sha256']) or (report.get('plan_sha256') != config['plan_sha256']) or (report.get('artifact') != config['worker']['artifact']) or (report.get('registered_selection') != config['worker']['pilot_selection']) or (sorted((row['native'] for row in report.get('geometry', []))) != config['worker']['geometry_captures']) or ([row['key'] for row in report.get('full_item_candidates', [])] != config['worker']['expected_keys']) or (report.get('geometry_refusal_policy') != M.GEOMETRY_REFUSAL_POLICY) or (not parity.get('pass')) or (run / 'native/R1.json').exists() or (run / 'native/probe/COMPLETE.json').exists() |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_job.py` | 152 | error branch with condition | report.get('selection') != selection or report.get('pilot_status') != selection['status'] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_job.py` | 162 | error branch with condition | report.get('phase') != 'insufficient_passing_coverage' or report.get('complete') is not False or report.get('items') |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_job.py` | 168 | error branch with condition | report.get('synthetic') is not False or report.get('artifact') != config['worker']['artifact'] or report.get('geometry_captures') != M.GEOMETRY_CAPTURES or (report.get('geometry_capture_ids') != config['worker']['geometry_captures']) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_job.py` | 210 | error branch with condition | proof['source'] != evidence['storage']['source'] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_launcher.py` | 28-29,34,36-37,39-42,44-45,47-50,52-55,65-66,70-71,75-76,78-79,83-84,86-87,92,98,100,102-104,106-110,122-123,125,128,130,132,136-145,149-155,159,163-164,166-167,169-173,176-178,193-195,197-199,203-211,213,215-218,220-221,223,225,227,229-232,234-239,242-245,248-249,252-255,259-273,276-277,279-280,284 | Orchard-only staging | inherited allocation or return transport |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_launcher.py` | 35 | error branch with condition | set(contract) != C.WORKER_FIELDS |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_launcher.py` | 38 | error branch with condition | L.canonical(direct) != DIRECT_DIGEST |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_launcher.py` | 46 | error branch with condition | entrypoint.get('path') not in code_pins or code_pins[entrypoint['path']] != entrypoint.get('sha256') |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_launcher.py` | 51 | error branch with condition | C.sha(source) != mask['sha256'] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_launcher.py` | 77 | error branch with condition | script.count(before) != 1 |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_launcher.py` | 85 | error branch with condition | {name: C.sha(path) for name, path in sources.items()} != family['bootstrap_pins'] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_launcher.py` | 99 | error branch with condition | mode == 'full' and projection_scenario not in M.SCENARIOS |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_launcher.py` | 101 | error branch with condition | mode != 'full' and projection_scenario is not None |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_launcher.py` | 105 | error branch with condition | destination.exists() |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_launcher.py` | 124 | error branch with condition | pilot_receipt is None or pilot_archive is None |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_launcher.py` | 129 | error branch with condition | config['full_projection']['report']['artifact'] != config['worker']['artifact'] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_launcher.py` | 131 | error branch with condition | pilot_receipt is not None or pilot_archive is not None |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_launcher.py` | 165 | error branch with condition | not match |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_launcher.py` | 168 | error branch with condition | render_batch(bundle, config['token']) != script |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_launcher.py` | 175 | error branch with condition | not entry.isfile() or entry.name in files or len(files) >= 64 or (entry.size < 0) or (total > 32 * 1024 ** 2) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_launcher.py` | 179 | error branch with condition | files != batch_files(config, family, review, order) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_launcher.py` | 196 | error branch with condition | command[-1].count(before) != 1 |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_launcher.py` | 212 | error branch with condition | C.sha(destination / name) != config[field]['sha256'] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_launcher.py` | 214 | error branch with condition | C.sha(destination / 'ORDER.md') != config['authorization']['orch_order']['sha256'] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_launcher.py` | 219 | error branch with condition | (destination / 'SUBMIT_INTENT.json').exists() |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_launcher.py` | 228 | error branch with condition | queue.returncode |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_launcher.py` | 233 | error branch with condition | any((line.split('/')[0] == '169097' or '/a15_cot_ap' in line for line in lines)) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_local_check.py` | 39-40,42,44-49,53-56,58,60-61,65-67,69-70,72,74,78,82-83,85-86,88-90,92,95-96,98-100,102,112-118,120-122,124-127,132-133,136,140-147,151-156,158-160,164,167-168,170-171,173-174,176,178-179,181,183-188,190-192,194-205,207,222-223,227,229-232,241,243-245,248-249,251-253,257-261,264-266,268-272,275-281,283-287,289-290,296-298,301-302,306-307,309-311,313-315 | Orchard-only staging | inherited allocation or return transport |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_local_check.py` | 41 | error branch with condition | len(parts) != 5 or {part['role'] for part in parts} != ROLES |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_local_check.py` | 43 | error branch with condition | sum((part['bytes'] for part in parts)) >= 1000000000 |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_local_check.py` | 57 | error branch with condition | family['assets'][key] != baseline['assets'][key] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_local_check.py` | 59 | error branch with condition | family['bootstrap_pins']['native_bootstrap.py'] != baseline['bootstrap_pins']['native_bootstrap.py'] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_local_check.py` | 64 | error branch with condition | set(contract) != set(approved['worker_contract']) or any((contract[key] != value for key, value in approved['worker_contract'].items() if key not in ('mask_cache', 'adapter_pins', 'kernel_source_pins', 'pilot_selection'))) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_local_check.py` | 68 | error branch with condition | set(contract['adapter_pins']) != set(old_adapters) / {new_adapter, str(C.LOGICAL_ROOT / 'native/out2/gravity_guard.py')} |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_local_check.py` | 71 | error branch with condition | name not in PACKAGING and contract['adapter_pins'].get(name) != digest |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_local_check.py` | 73 | error branch with condition | any((digest != family['code_pins'].get(name) for name, digest in contract['adapter_pins'].items())) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_local_check.py` | 77 | error branch with condition | set(contract['kernel_source_pins']) != {'nomdg', 'geometry'} or any((digest != family['code_pins'].get(str(C.LOGICAL_ROOT / 'native/out2' / (name + '.py'))) for name, digest in contract['kernel_source_pins'].items())) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_local_check.py` | 81 | error branch with condition | contract['pilot_selection'].get('families') != G.K.PILOT_COUNTS or contract['pilot_selection'].get('distance_datasets') != G.K.DISTANCE_DATASETS or len(contract['pilot_selection'].get('item_keys', [])) != 10 |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_local_check.py` | 84 | error branch with condition | set(family['code_pins']) != expected |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_local_check.py` | 87 | error branch with condition | name not in PACKAGING and digest != approved['code_pins'][name] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_local_check.py` | 91 | error branch with condition | entrypoint != dict(path=worker_path, sha256=family['code_pins'][worker_path]) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_local_check.py` | 94 | error branch with condition | contract['mask_cache'].get('path') != G.MASK_PATH or contract['mask_cache'].get('sha256') != family['code_pins'].get(G.MASK_PATH) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_local_check.py` | 97 | error branch with condition | key not in ('small_objects', 'worker_entrypoint') and family['assets'][key] != baseline['assets'][key] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_local_check.py` | 101 | error branch with condition | part['role'] != 'code' and part != old_parts[part['role']] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_local_check.py` | 119 | error branch with condition | family['code_pins'].get(logical) != digest |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_local_check.py` | 123 | error branch with condition | type(value.get('step')) is not int |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_local_check.py` | 135 | error branch with condition | not source.is_absolute() or source.is_symlink() or (not source.is_file()) or (not source.resolve().is_relative_to(LANE)) or (source.stat().st_size >= 1024 ** 2) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_local_check.py` | 157 | error branch with condition | set(local_objects) != ROLES |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_local_check.py` | 163 | error branch with condition | not path.is_absolute() or path.is_symlink() or (not path.is_file()) or (not path.resolve().is_relative_to(LANE)) or (path.stat().st_size != identities[name]['bytes']) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_local_check.py` | 166 | error branch with condition | root.exists() or root.is_symlink() or (not root.parent.is_dir()) or (not root.resolve().is_relative_to(LANE)) or output.exists() |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_local_check.py` | 169 | error branch with condition | shutil.disk_usage(root.parent).free - required < 200 * 1024 ** 3 |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_local_check.py` | 175 | error branch with condition | part not in family['assets']['small_objects'] or assets != family['assets'] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_local_check.py` | 180 | error branch with condition | item != family['assets']['runtime'] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_local_check.py` | 193 | error branch with condition | not reached or set(staged) != {'small_' + name for name in ROLES} |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_local_check.py` | 206 | error branch with condition | not graph['inputs_passed'] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_local_check.py` | 240 | error branch with condition | record.get('schema') != SCHEMA or record.get('passed') is not True or record.get('synthetic') is not False or (record.get('family', {}).get('sha256') != config['family']['sha256']) or (record.get('helper', {}).get('sha256') != C.sha(__file__)) or (record.get('objects') != objects(family['assets'])) or (record.get('production_interpreter_executed') is not False) or (record.get('gpu_worker_executed') is not False) or (record.get('network_calls') != 0) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_local_check.py` | 242 | error branch with condition | record.get('runtime_equality') != scope(family) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_local_check.py` | 247 | error branch with condition | record.get('comparison_helper', {}).get('sha256') != C.sha(G.__file__) or graph['family']['sha256'] != config['family']['sha256'] or graph['inputs_passed'] is not True |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_local_check.py` | 250 | error branch with condition | root.is_symlink() or not root.is_dir() or (not root.resolve().is_relative_to(LANE)) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_local_check.py` | 256 | error branch with condition | metadata.get('source', {}).get('sha256') != artifact['sha256'] or metadata.get('staged') != dict(path=str(S.physical(root, artifact['path'])), sha256=artifact['sha256']) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_local_check.py` | 263 | error branch with condition | Path(archive['path']) != root / 'archives' / (name + '.tar') or archive['sha256'] != record['objects'][name]['sha256'] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_local_check.py` | 267 | error branch with condition | checks != record['input_pin_checks'] or checks['step'] != config['step'] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_local_check.py` | 273 | error branch with condition | target.read_bytes() != data |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_local_check.py` | 282 | error branch with condition | any(present) and (not all(present)) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_local_check.py` | 299 | error branch with condition | C.load(target) != result |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_metrics.py` | 28,31-32,35,39-40,42-49,53-54,56,191-192,195-196,396,398-399,401-402,404-405,421-422,424,426,430,432-440,442-445,447,449,453-454 | Orchard-only staging | inherited allocation or return transport |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_metrics.py` | 41 | error branch with condition | len(set(files)) != len(files) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_metrics.py` | 71 | error branch with condition | not row.get('geometry_refusal') or row.get('decode_executed') is not False or 'decode' in row or (row.get('called') is not False) or row.get('call_errors') or row.get('version_errors') or any((value not in (None, 0.0) for value in row['scores'].values())) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_metrics.py` | 74 | error branch with condition | name not in FAMILY_COUNTS |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_metrics.py` | 83 | error branch with condition | len(identities) != len(set(identities)) or set(identities) != {(key, arm) for key in keys for arm in ('unflagged', 'scripted')} |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_metrics.py` | 100 | error branch with condition | report.get('geometry_refusal_policy') != GEOMETRY_REFUSAL_POLICY or len(geometry) != GEOMETRY_CAPTURES or len({row['native'] for row in geometry}) != GEOMETRY_CAPTURES or any((row.get('status') not in ('PASS', 'REFUSED') for row in geometry)) or (len(candidates) != 636) or (len({row['key'] for row in candidates}) != 636) or ({row['native'] for row in candidates} != {row['native'] for row in geometry}) or (Counter((row['family'] for row in candidates)) != Counter(FAMILY_COUNTS)) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_metrics.py` | 107 | error branch with condition | len(identities) != len(set(identities)) or set(identities) != {(key, arm) for key in expected_refusals for arm in ('unflagged', 'scripted')} |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_metrics.py` | 118 | error branch with condition | refusal.get('capture') != capture['native'] or refusal.get('checkpoint') != report['artifact'] or refusal.get('code') != GEOMETRY_REFUSAL_CODE or (refusal.get('capture_record_sha256') != C.canonical(recorded)) or (refusal.get('code') != capture['error']['code']) or (refusal.get('message') != capture['error']['message']) or (row.get('binding') != report.get('request_binding')) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_metrics.py` | 123 | error branch with condition | dict(refused_counts) != report.get('geometry_refused_items') or refused_sizes != report.get('refusal_return_size') |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_metrics.py` | 204 | error branch with condition | type(value) is not int or value < 0 |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_metrics.py` | 213 | error branch with condition | scenario is not None and scenario not in SCENARIOS |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_metrics.py` | 231 | error branch with condition | report.get('schema') != 'evalx-unscored-native-pilot-report-v1' or report.get('synthetic') is not False or report.get('complete') is not True or (report.get('training_decision_allowed') is not False) or (report.get('full_read_authorized') is not False) or (report.get('parity_pass') is not True) or (report.get('full_family_counts') != FAMILY_COUNTS) or (report.get('full_geometry_captures') != GEOMETRY_CAPTURES) or (report.get('geometry_refusal_policy') != GEOMETRY_REFUSAL_POLICY) or (len(items) != 10) or (len(geometry) != GEOMETRY_CAPTURES) or (len({row['native'] for row in geometry}) != GEOMETRY_CAPTURES) or ([row['key'] for row in items] != selection.get('item_keys')) or (len(set(selection.get('item_keys', []))) != 10) or (Counter((row['family'] for row in items)) != Counter(K.PILOT_COUNTS)) or (selection.get('families') != K.PILOT_COUNTS) or (selection != K.select_geometry_pilot(report.get('full_item_candidates', []), report.get('registered_selection', {}), geometry)) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_metrics.py` | 237 | error branch with condition | bool(row.get('geometry_refusal')) != refused |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_metrics.py` | 241 | error branch with condition | refused and (row.get('decode_executed') is not False or row.get('generated_tokens') != 0 or row.get('native_seconds') != 0 or (row.get('finish') != 'geometry_refusal') or row.get('call_errors') or row.get('capped') or row.get('decode_budget')) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_metrics.py` | 247 | error branch with condition | report.get('decode_budget') != budget or report.get('query_journal_retain_per_type') != 3 or report.get('reader_semantics') != C.REPORT_SEMANTICS |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_metrics.py` | 252 | error branch with condition | close_lengths and close_tokens < 1 |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_metrics.py` | 266 | error branch with condition | any(('digested_journal_gzip_bytes' not in row or 'digested_journal_raw_bytes' not in row for row in sizes)) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_metrics.py` | 298 | error branch with condition | not sampled or sampled + injected != total or row['capped'] is not capped or (timing.get('total_tokens', total) != total) or any((not math.isfinite(row[field]) or row[field] < 0 for field in ('seconds', 'native_seconds'))) or (row['native_seconds'] > row['seconds']) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_metrics.py` | 331 | error branch with condition | any((type(value) not in (int, float) or not math.isfinite(value) or value < 0 for value in times)) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_metrics.py` | 333 | error branch with condition | geometry_seconds < sum((row['seconds'] for row in geometry)) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_metrics.py` | 336 | error branch with condition | not math.isfinite(overhead) or overhead < 0 |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_metrics.py` | 348 | error branch with condition | not math.isfinite(seconds) or seconds < 0 |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_metrics.py` | 397 | error branch with condition | not isinstance(evidence, dict) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_metrics.py` | 400 | error branch with condition | report.get('artifact') != artifact |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_metrics.py` | 403,431 | error branch with condition | scenario not in SCENARIOS |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_metrics.py` | 420 | error branch with condition | report.get('family_sha256') != family_sha256 or complete.get('family', {}).get('sha256') != family_sha256 or complete.get('mode') != 'pilot' or (complete.get('synthetic') is not False) or (complete.get('training_decision_allowed') is not False) or (complete.get('artifact') != report.get('artifact')) or (receipt.get('synthetic') is not False) or (receipt.get('status') != 'COMPLETE') or (receipt.get('complete') is not True) or (receipt.get('returncode') != 0) or (not report.get('plan_sha256')) or (report['plan_sha256'] != complete.get('plan_sha256')) or (report['plan_sha256'] != receipt.get('plan_sha256')) or (parity.get('pass') is not True) or (parity.get('p1_gate', {}).get('pass') is not True) or any((parity.get(name, {}).get('pass') is not True for name in ('P2', 'P3'))) or (parity.get('camera_call') is not True) or parity.get('call_errors') or (evidence.get('report_canonical_sha256') != C.canonical(report)) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_metrics.py` | 423 | error branch with condition | projection != evidence.get('projection') |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_metrics.py` | 425 | error branch with condition | not projection['fits'] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_metrics.py` | 441 | error branch with condition | entry.size > 2 * 1024 ** 2 |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_metrics.py` | 446 | error branch with condition | complete.get('receipts', {}).get(name) != hashlib.sha256(raw[name]).hexdigest() |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_metrics.py` | 448 | error branch with condition | report.get('parity', {}).get('sha256') != hashlib.sha256(raw[names[2]]).hexdigest() |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_pin_graph.py` | 108,113-120,124-131,133,135-137,141-144,146-151,153-155,157,160-174,177-182,184-190,192,195,198-199,201-203,206-209,211,219-221,223-232,234-236,238-244,246-248,257-260,262-264,266-282,284-292,294,301-302,304-309,311-317,320,322,325,329-335,341-343,346,351,353,355-356,358-363,365,369,371-376,378-382,384-385,388,391-395,397-400,402-409,412-413,415-419,421-423,425-440,442-443,445-447,449-450,452-453,455-459,463,465-469,472,476-479,491-494,496-498 | Orchard-only staging | inherited allocation or return transport |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_pin_graph.py` | 109 | error branch with condition | not condition |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 26-27,29-31,35-36,41,67,103,105,110-118,131,135-136,138-139,144,146,152,161-163,167-168,173,176-178,181-182,184,186-188,191-192,196-198,200-205,207-211,213,217-219,221,223,226-227,232-233,235,239-241,243-244,246,248,250,252-258,260-264,266,268-272,274,276-282,284-285,287-289,291-298,300-305,307-313,315,317-322,324-325,327-328,336,338-340,345-347,349-356,358-361,363-372,374-376,379-380,384-386,388,390-391,393-394,396-401,403-405,407-416,418-424,426-429,431-432,434-436,439-447,449,451-452,454-456,458-461,463-475,477-478,480-485,490,492-495,498,500-504 | Orchard-only staging | inherited allocation or return transport |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 28 | error branch with condition | not path.is_absolute() or '..' in path.parts |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 40 | error branch with condition | not re.fullmatch('[a-z0-9_-]+/[A-Za-z0-9_./-]+', name) or '..' in Path(name).parts or (not str(record.get('generation', '')).isdigit()) or (not re.fullmatch('[0-9a-f]{64}', record.get('sha256', ''))) or (type(record.get('bytes')) is not int) or (record['bytes'] <= 0) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 50 | error branch with condition | not re.fullmatch('[0-9a-f]{64}', digest) or name in result |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 53 | error branch with condition | not result or len(result) > 20000 |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 65,101 | error branch with condition | count >= 200000 |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 74 | error branch with condition | name in inventory or not entry.isfile() or entry.size < 0 or (total > Path(path).stat().st_size) or (entry.size > record.get('max_bytes', 8 * 1024 ** 3)) or ('bytes' in record and entry.size != record['bytes']) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 78 | error branch with condition | target.is_symlink() or not target.parent.resolve().is_relative_to(root.resolve()) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 85 | error branch with condition | output.write(chunk) != len(chunk) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 87 | error branch with condition | copied != entry.size or digest.hexdigest() != record['sha256'] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 91 | error branch with condition | set(inventory) != set(wanted) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 104 | error branch with condition | entry.linkname not in RUNTIME_LINKS.get(name, ()) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 137 | error branch with condition | not path.is_absolute() or '..' in path.parts or path.is_symlink() |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 145 | error branch with condition | not record['name'].startswith(assets['cloud_prefix'] + '/') |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 153-156 | error branch with condition | actual != expected |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 183 | error branch with condition | required and (found is None or not found.resolve().is_relative_to(Path(paths[required]).resolve())) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 185 | error branch with condition | found is None |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 190 | error branch with condition | not ptxas.is_file() or not ptxas.resolve().is_relative_to((root / 'fla/p').resolve()) or (not os.access(ptxas, os.X_OK)) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 199 | error branch with condition | S.sha(puller) != assets['frame_puller']['sha256'] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 220 | error branch with condition | not 0 <= start <= end < part['bytes'] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 231 | error branch with condition | response.status != 206 or response.headers.get('x-goog-generation') != generation or response.headers.get('Content-Encoding') not in (None, 'identity') or (response.headers.get('Content-Length') != str(end - start + 1)) or (response.headers.get('Content-Range') != f"bytes {start}-{end}/{part['bytes']}") |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 234 | error branch with condition | len(data) != end - start + 1 |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 242 | error branch with condition | total != transport['archive_bytes'] or not parts |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 249 | error branch with condition | size < 0 or offset < 0 or offset + size > total |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 251 | error branch with condition | consumed + size > 2 * 1024 ** 2 |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 259 | error branch with condition | len(requests) >= 300 |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 265 | error branch with condition | len(chunk) != count |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 273 | error branch with condition | len(data) != size |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 283 | error branch with condition | count <= space - offset + 1 or end > len(data) or data[end - 1:end] != b'\n' |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 286 | error branch with condition | key.startswith('GNU.sparse') |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 299 | error branch with condition | pending or read(offset, 512) != b'\x00' * 512 |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 306 | error branch with condition | member.size < 0 |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 323 | error branch with condition | name in seen or size < 0 or offset + (size + 511) // 512 * 512 > total |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 337 | error branch with condition | not value['members'] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 341 | error branch with condition | path.parts[0] != 'm' + str(step) or member['type'] not in ('0', '\x00', '5') |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 348 | error branch with condition | target.is_symlink() or not target.resolve().is_relative_to(root.resolve()) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 357 | error branch with condition | relative in expected |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 362 | error branch with condition | target.exists() and (not target.is_dir()) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 377 | error branch with condition | unexpected or missing |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 402 | error branch with condition | total >= 1000000000 or len(assets['small_objects']) != 5 |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 430 | error branch with condition | len(present) != 1 |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 448 | error branch with condition | S.sha(manifest) != assets['fla']['manifest']['sha256'] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 453 | error branch with condition | source.stat().st_size != assets['fla']['bytes'] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 462 | error branch with condition | S.sha(physical(root, assets['model_manifest']['path'])) != assets['model_manifest']['sha256'] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 479 | error branch with condition | authentication.returncode or not token or '\n' in token or ('\r' in token) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 491 | error branch with condition | receipt['bytes'] != transport['archive_bytes'] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 497 | error branch with condition | {name: row['bytes'] for name, row in inventory.items()} != {row['name']: row['size'] for row in headers['members'] if row['type'] in ('0', '\x00')} |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_stage.py` | 499 | error branch with condition | S.sha(physical(root, config['worker']['artifact']['path'])) != config['worker']['artifact']['sha256'] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_worker.py` | 17-23,27-30,32-33,36,39,41,45-46,55-61,77-79,83-86,88-94,96,100-101,104-105,107,122-123,125-131,133-134,138-143,146-154,157-159,161-166,169-171,173,176-177,179-180,182-184,189-193,195-207,209-212,214,217-222,224-225,227-230,241-242,244-255,257,270,274-278,280,282-283,288,296-297,301-307,316-327,329-330,333-335,344,348-349,354-355,359-362,366 | Orchard-only staging | inherited allocation or return transport |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_worker.py` | 31 | error branch with condition | len(captures) != 152 or len(keys) != 636 or keys != worker['expected_keys'] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_worker.py` | 35 | error branch with condition | names != worker['geometry_captures'] or len(names) != M.GEOMETRY_CAPTURES or Counter((N.family(task['question_type']) for task in chosen)) != Counter(M.FAMILY_COUNTS) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_worker.py` | 40 | error branch with condition | selection != worker['pilot_selection'] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_worker.py` | 87 | error branch with condition | not set(required) <= allowed <= set(by_name) or len(required) > 5 |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_worker.py` | 95 | error branch with condition | len(names) != 5 |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_worker.py` | 103 | error branch with condition | len(required) != M.GEOMETRY_CAPTURES or len(set(required)) != M.GEOMETRY_CAPTURES or len({row['native'] for row in captures}) != len(captures) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_worker.py` | 106 | error branch with condition | {capture['native'] for capture in selected} != set(required) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_worker.py` | 226 | error branch with condition | not set(required) <= {record['native'] for record in geometry_times} |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_worker.py` | 279 | error branch with condition | len(timings) != 10 or (output / 'COMPLETE.json').exists() |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/native_worker.py` | 353 | error branch with condition | not os.environ.get('SLURM_JOB_ID', '').isdigit() or not os.uname().nodename.startswith('orchard-') or len(os.environ.get('CUDA_VISIBLE_DEVICES', '').split(',')) != 1 or (not os.environ.get('CUDA_VISIBLE_DEVICES')) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/producer_bridge/sa/prestage_hooks.py` | 1-21,23-25,27-29,31-32,34,36-39,41-42,44-47,49,51-56,58-60,62-66,68-77,79-87,89-91,93,95-99,101-102,104-125,127-135,137-147,149-150,152-164,166-168,170-179,181-189,191-192,194-195,197-203,205-212,214-224,226-227,229-257,259-263,265-279,281-286,288-297,299-300,302-309,311-313,315-318,320-338,340-343,345-351,353-361,363-370,372-375,377-379,381-407,409-471,473-478,480-497,499-500 | Orchard-only staging | inherited allocation or return transport |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/producer_bridge/sa/prestage_hooks.py` | 40 | error branch with condition | hashlib.sha256(raw).hexdigest() != os.environ['R1_PRESTAGE_RECEIPT_SHA256'] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/producer_bridge/sa/prestage_hooks.py` | 43 | error branch with condition | self.receipt.get('schema') != 'r1-prestage-receipt-v1' |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/producer_bridge/sa/prestage_hooks.py` | 48 | error branch with condition | self.receipt.get('format') != 'r1-prestage-v2' or self.stamp.get('schema') != 'r1-prestage-verify-v1' or self.stamp.get('manifest') != {'path': manifest['path'], 'sha256': manifest['sha256'], 'bytes': manifest['stat'][0], 'mtime_ns': manifest['stat'][1]} or (type(self.stamp.get('shards')) is not list) or (not self.stamp['shards']) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/producer_bridge/sa/prestage_hooks.py` | 50 | error branch with condition | not self.inputs_unchanged(None) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/producer_bridge/sa/prestage_hooks.py` | 92 | error branch with condition | len(data) != item['bytes'] or hashlib.sha256(data).hexdigest() != item['sha256'] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/producer_bridge/sa/prestage_hooks.py` | 100 | error branch with condition | hashlib.sha256(data).hexdigest() != item['sha256'] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/producer_bridge/sa/prestage_hooks.py` | 204 | error branch with condition | len(manifest['rows']) != state.receipt['rows'] or manifest['counts'] != state.receipt['counts'] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/producer_bridge/sa/prestage_hooks.py` | 258 | error branch with condition | present != {item['staged']['sha256']: item['bytes'] for item in files} |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/producer_bridge/sa/prestage_hooks.py` | 280 | error branch with condition | text.count(item['placeholder'].encode()) != item['references'] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/producer_bridge/sa/prestage_hooks.py` | 287 | error branch with condition | path.exists() |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/producer_bridge/sa/prestage_hooks.py` | 310 | error branch with condition | receipt.get('schema') != 'student-frame-staging-v1' or module.digest_json(receipt) != receipt_pin['sha256'] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/producer_bridge/sa/prestage_hooks.py` | 314 | error branch with condition | declared != expected or len(declared) != len(files) or receipt.get('unique_frames') != len(files) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/producer_bridge/sa/prestage_hooks.py` | 319 | error branch with condition | len(digest) != 64 or any((character not in '0123456789abcdef' for character in digest)) or item['source']['sha256'] != digest or (destination != root / 'frames' / digest[:2] / digest) or destination.is_symlink() or (destination.resolve() != destination) or (type(item['bytes']) is not int) or (item['bytes'] < 0) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/producer_bridge/sa/prestage_hooks.py` | 344 | error branch with condition | destination.stat().st_size != item['bytes'] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/producer_bridge/sa/sitecustomize.py` | 1-18,20-21,23-25,27-28,30-32,34,36-39,41-47,49-50,52-62,64-65,67-71,73,75-80,82-83,85,87-89,91,93-101,103-104,106-109 | Orchard-only staging | inherited allocation or return transport |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/producer_bridge/sa/sitecustomize.py` | 22 | error branch with condition | hashlib.sha256(data).hexdigest() not in MODULE_SHA256 |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/producer_bridge/sa/sitecustomize.py` | 26 | error branch with condition | len(positions) != 1 |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/producer_bridge/sa/sitecustomize.py` | 29 | error branch with condition | len(commands) != 1 or ast.unparse(tree.body[commands[0]]) != COMMAND_SOURCE or commands[0] < positions[0] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/producer_bridge/sa/sitecustomize.py` | 81 | error branch with condition | not callable(getattr(module, 'prefetched_batches', None)) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_native/producer_bridge/sa/sitecustomize.py` | 105 | error branch with condition | not spec.origin or not spec.origin.endswith('.py') |
| `code/sj/orch_cd/evalx/work/milestone/orchard_results.py` | 26-30,34,39,43-48,50,52-53,55-58,60-61,63-70,74,76,82-84,87-91,93-95,98,100-101,103,106,108,112-113,115,117,119,121,125,127-137,139,143-146,148,150,154-155,157-163,166-167,169-174,176-180,182-184,187-188,191-192,194-195,197-201,203,205-208,210-214,216-220,222-225,227,232-234,236-238,240-245,249-251,253-257,259-261,263-282,284-292,297,299-307,310-315,318-320,322-325,327-329,341-342,344,346-349,353-354,358-359,361-371,374-378,382-386,390,392 | Orchard-only staging | inherited allocation or return transport |
| `code/sj/orch_cd/evalx/work/milestone/orchard_results.py` | 54 | error branch with condition | not generation.isdigit() or int(meta.get('size', -1)) != path.stat().st_size |
| `code/sj/orch_cd/evalx/work/milestone/orchard_results.py` | 62 | error branch with condition | check.stat().st_size != path.stat().st_size or digest != sha(path) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_results.py` | 75 | error branch with condition | receipt.get('synthetic') is not False |
| `code/sj/orch_cd/evalx/work/milestone/orchard_results.py` | 81 | error branch with condition | receipt.get('schema') != 'evalx-orchard-result-return-v1' or receipt.get('plan_sha256') != expected_plan or receipt.get('status') != 'COMPLETE' or (receipt.get('complete') is not True) or (receipt.get('conflicting_terminal_markers') is not False) or (receipt.get('returncode') != 0) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_results.py` | 86 | error branch with condition | archive.is_symlink() or archive.stat().st_size != pin.get('bytes') or archive.stat().st_size > mode_limit(receipt.get('mode', 'pilot')) - EXIT_RESERVE or (sha(archive) != pin.get('sha256')) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_results.py` | 92 | error branch with condition | entry.name in names or len(names) >= 10000 or entry.size < 0 or (total > 512 * 1024 ** 2) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_results.py` | 97 | error branch with condition | not entry.isfile() or path.is_absolute() or '..' in path.parts or (path.suffix in ('.pt', '.safetensors', '.png', '.jpg', '.jpeg')) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_results.py` | 99 | error branch with condition | 'FAILED.json' in names or 'COMPLETE.json' not in names |
| `code/sj/orch_cd/evalx/work/milestone/orchard_results.py` | 102 | error branch with condition | marker.get('plan_sha256') != expected_plan or marker.get('synthetic') is not False |
| `code/sj/orch_cd/evalx/work/milestone/orchard_results.py` | 107 | error branch with condition | mode not in ('pilot', 'full') |
| `code/sj/orch_cd/evalx/work/milestone/orchard_results.py` | 114 | error branch with condition | not re.fullmatch('[a-z][0-9a-f]{8,32}', token) or not 0 < rate <= 4 * 1024 ** 2 |
| `code/sj/orch_cd/evalx/work/milestone/orchard_results.py` | 116 | error branch with condition | not pool.is_absolute() or '..' in pool.parts |
| `code/sj/orch_cd/evalx/work/milestone/orchard_results.py` | 120 | error branch with condition | synthetic and (not pool.is_relative_to(allowed)) or (not synthetic and pool != allowed) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_results.py` | 138 | error branch with condition | process.returncode |
| `code/sj/orch_cd/evalx/work/milestone/orchard_results.py` | 147 | error branch with condition | time.monotonic() - started > 60 |
| `code/sj/orch_cd/evalx/work/milestone/orchard_results.py` | 149 | error branch with condition | result.get('verified') is not True or result.get('bytes') != 4 * 1024 ** 2 |
| `code/sj/orch_cd/evalx/work/milestone/orchard_results.py` | 156 | error branch with condition | pool.is_symlink() or not pool.is_absolute() or (not re.fullmatch('[a-z][0-9a-f]{8,32}', token)) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_results.py` | 164 | error branch with condition | usage(pool) + len(data) + EXIT_RESERVE > POOL_LIMIT |
| `code/sj/orch_cd/evalx/work/milestone/orchard_results.py` | 168 | error branch with condition | stream.write(data) != len(data) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_results.py` | 175 | error branch with condition | actual != expected |
| `code/sj/orch_cd/evalx/work/milestone/orchard_results.py` | 181 | error branch with condition | not dest.is_dir() or dest.is_symlink() |
| `code/sj/orch_cd/evalx/work/milestone/orchard_results.py` | 186 | error branch with condition | value['token'] != token or value['plan_sha256'] != exit_value['plan_sha256'] or value['job'] != exit_value['job'] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_results.py` | 190 | error branch with condition | size > EXIT_RESERVE or usage(dest) + size > mode_limit(exit_value['mode']) or usage(pool) + size > POOL_LIMIT |
| `code/sj/orch_cd/evalx/work/milestone/orchard_results.py` | 193 | error branch with condition | sha(dest / 'RETURN_RECEIPT.json') != sha(local / 'RETURN_RECEIPT.json') |
| `code/sj/orch_cd/evalx/work/milestone/orchard_results.py` | 196 | error branch with condition | action != 'publish' or not 0 < rate <= 4 * 1024 ** 2 |
| `code/sj/orch_cd/evalx/work/milestone/orchard_results.py` | 202 | error branch with condition | size > mode_limit(receipt['mode']) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_results.py` | 204 | error branch with condition | usage(pool) + size + EXIT_RESERVE > POOL_LIMIT |
| `code/sj/orch_cd/evalx/work/milestone/orchard_results.py` | 215 | error branch with condition | output.write(data) != len(data) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_results.py` | 221 | error branch with condition | partial.stat().st_size != (local / name).stat().st_size or sha(partial) != sha(local / name) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_results.py` | 235 | error branch with condition | not re.fullmatch('[0-9a-f]{64}', plan_sha256) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_results.py` | 239 | error branch with condition | not Path(cloud_config).is_absolute() |
| `code/sj/orch_cd/evalx/work/milestone/orchard_results.py` | 262 | error branch with condition | (local / 'EXIT.json').stat().st_size > EXIT_RESERVE or usage(local) > cap |
| `code/sj/orch_cd/evalx/work/milestone/orchard_results.py` | 283 | error branch with condition | sum(((local / n).stat().st_size for n in ('result.tar.gz', 'EXIT.json', 'JOB.log', 'RETURN_RECEIPT.json'))) > cap |
| `code/sj/orch_cd/evalx/work/milestone/orchard_results.py` | 298 | error branch with condition | submission.get('status') != 'SUBMITTED' |
| `code/sj/orch_cd/evalx/work/milestone/orchard_results.py` | 321 | error branch with condition | described.returncode |
| `code/sj/orch_cd/evalx/work/milestone/orchard_results.py` | 326 | error branch with condition | not generation.isdigit() or not 0 < size <= limit |
| `code/sj/orch_cd/evalx/work/milestone/orchard_results.py` | 343 | error branch with condition | result.returncode or len(result.stdout) > limit |
| `code/sj/orch_cd/evalx/work/milestone/orchard_results.py` | 345 | error branch with condition | channel == 'gcs' and len(result.stdout) != objects[name]['bytes'] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_results.py` | 352 | error branch with condition | value.get('token') != token or str(value.get('job')) != str(submission['job']) or value.get('plan_sha256') != config['plan_sha256'] or (value.get('synthetic') is not False) or (value.get('mode', 'pilot') != config.get('mode', 'pilot')) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_results.py` | 357 | error branch with condition | pin.get('name') != 'result.tar.gz' or type(pin.get('bytes')) is not int or (not 0 < pin['bytes'] <= cap - EXIT_RESERVE) or (not re.fullmatch('[0-9a-f]{64}', pin.get('sha256', ''))) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_results.py` | 360 | error branch with condition | len(data) != pin['bytes'] or hashlib.sha256(data).hexdigest() != pin['sha256'] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_results.py` | 373 | error branch with condition | proof.get('token') != token or proof.get('plan_sha256') != config['plan_sha256'] or str(proof.get('job')) != str(submission['job']) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_results.py` | 391 | error branch with condition | len(sys.argv) not in (6, 7) or sys.argv[1] != '--pool-worker' |
| `code/sj/orch_cd/evalx/work/milestone/orchard_stage.py` | 28-32,36,54,56,73-74,77-79,82-83,85,87-88,90-91,93-94,98,100,117-120,122-133,135-138,140-142,144,146-148,150-151,156,159,161,166-167,169-171,174-181,185-186,190,197-200,202-203,205,209-212,214,216-217,220-221,223-229,232-240,242-253,255-258,260-261,263-266,268-270,272-275,278-279,282-283,285-290,292-296,298-303,305-308 | Orchard-only staging | inherited allocation or return transport |
| `code/sj/orch_cd/evalx/work/milestone/orchard_stage.py` | 37 | error branch with condition | shutil.disk_usage(path).free < MIN_FREE + extra |
| `code/sj/orch_cd/evalx/work/milestone/orchard_stage.py` | 43 | error branch with condition | path.is_absolute() or '..' in path.parts or '\x00' in name |
| `code/sj/orch_cd/evalx/work/milestone/orchard_stage.py` | 55 | error branch with condition | not item.isdir() |
| `code/sj/orch_cd/evalx/work/milestone/orchard_stage.py` | 59 | error branch with condition | step is not None and path.parts[0] != 'm' + str(step) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_stage.py` | 61 | error branch with condition | str(path) in seen |
| `code/sj/orch_cd/evalx/work/milestone/orchard_stage.py` | 64 | error branch with condition | len(seen) > 200000 or item.size < 0 |
| `code/sj/orch_cd/evalx/work/milestone/orchard_stage.py` | 67 | error branch with condition | total > limit |
| `code/sj/orch_cd/evalx/work/milestone/orchard_stage.py` | 71 | error branch with condition | not parent.is_relative_to(destination) or target.is_symlink() |
| `code/sj/orch_cd/evalx/work/milestone/orchard_stage.py` | 80 | error branch with condition | RUNTIME_ABSOLUTE_LINKS.get(str(path)) != item.linkname |
| `code/sj/orch_cd/evalx/work/milestone/orchard_stage.py` | 84 | error branch with condition | '..' in link.parts[first_name:] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_stage.py` | 86 | error branch with condition | not Path(os.path.normpath(str(parent / str(link)))).is_relative_to(destination) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_stage.py` | 92 | error branch with condition | not source.resolve().is_relative_to(destination) or source.is_symlink() or (not source.is_file()) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_stage.py` | 96 | error branch with condition | not item.isfile() |
| `code/sj/orch_cd/evalx/work/milestone/orchard_stage.py` | 99 | error branch with condition | not target.is_file() |
| `code/sj/orch_cd/evalx/work/milestone/orchard_stage.py` | 108,139 | error branch with condition | output.write(chunk) != len(chunk) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_stage.py` | 110 | error branch with condition | copied != item.size |
| `code/sj/orch_cd/evalx/work/milestone/orchard_stage.py` | 121 | error branch with condition | destination.exists() or partial.exists() |
| `code/sj/orch_cd/evalx/work/milestone/orchard_stage.py` | 134 | error branch with condition | copied > part['bytes'] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_stage.py` | 143 | error branch with condition | copied != part['bytes'] or hashed.hexdigest() != part['sha256'] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_stage.py` | 145 | error branch with condition | part.get('md5') and base64.b64encode(md5.digest()).decode() != part['md5'] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_stage.py` | 149 | error branch with condition | expected_sha is not None and whole.hexdigest() != expected_sha |
| `code/sj/orch_cd/evalx/work/milestone/orchard_stage.py` | 160 | error branch with condition | not select.select([self.process.stdout], [], [], 300)[0] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_stage.py` | 172 | error branch with condition | process.wait(timeout=60) |
| `code/sj/orch_cd/evalx/work/milestone/orchard_stage.py` | 201 | error branch with condition | len(result) >= 256 |
| `code/sj/orch_cd/evalx/work/milestone/orchard_stage.py` | 241 | error branch with condition | sha(payload) != config['payload_sha256'] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_stage.py` | 254 | error branch with condition | source.stat().st_size != assets['base_archive_bytes'] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_stage.py` | 259 | error branch with condition | sha(manifest) != assets['base_manifest']['sha256'] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_stage.py` | 262 | error branch with condition | inventory.get(row['path']) != {key: row[key] for key in ('bytes', 'sha256')} |
| `code/sj/orch_cd/evalx/work/milestone/orchard_stage.py` | 284 | error branch with condition | receipts['export']['bytes'] != transport['archive_bytes'] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_stage.py` | 291 | error branch with condition | sha(physical(root, config['spec']['artifact']['path'])) != config['spec']['artifact']['sha256'] |
| `code/sj/orch_cd/evalx/work/milestone/orchard_stage.py` | 304 | error branch with condition | Path(name).suffix != '.png' or Path(name).stem != record['sha256'] |
| `code/sj/orch_cd/evalx/work/milestone/stdout_transfer.py` | 1-11,14-22,25-26,28,31-32,37,40-43,45,47-50,52-55,57-59,61,63-68,70-75,78-79,82-86,89-92,94-104,106-107,109-110,112-113,115-118,120-121,123-127,131-133,135-136,138-140,142-143,147-152,155-168,170-172,175-176 | UNEXPLAINED | No test or rehearsal executed this job-source line. |
| `code/sj/orch_cd/evalx/work/milestone/stdout_transfer.py` | 27 | error branch with condition | not isinstance(value, str) or re.fullmatch('[0-9a-f]{64}', value) is None |
| `code/sj/orch_cd/evalx/work/milestone/stdout_transfer.py` | 36 | error branch with condition | set(header) != {'schema', 'plan_sha256', 'sha256', 'bytes', 'outcome'} or header['schema'] != SCHEMA or header['plan_sha256'] != digest_string(plan) or (type(header['bytes']) is not int) or (not 0 < header['bytes'] <= LIMIT) or (header['outcome'] not in ('complete', 'failed')) |
| `code/sj/orch_cd/evalx/work/milestone/stdout_transfer.py` | 44 | error branch with condition | type(rate) is not int or not 0 < rate <= MAX_RATE |
| `code/sj/orch_cd/evalx/work/milestone/stdout_transfer.py` | 46 | error branch with condition | source.is_symlink() or not stat.S_ISREG(source.stat().st_mode) |
| `code/sj/orch_cd/evalx/work/milestone/stdout_transfer.py` | 51 | error branch with condition | not stat.S_ISREG(before.st_mode) or not 0 < before.st_size <= LIMIT |
| `code/sj/orch_cd/evalx/work/milestone/stdout_transfer.py` | 77 | error branch with condition | (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (after.st_size, after.st_mtime_ns, after.st_ctime_ns) |
| `code/sj/orch_cd/evalx/work/milestone/stdout_transfer.py` | 88 | error branch with condition | not parent.is_dir() or parent.parts[1:2] == ('home',) or (len(parent.parts) > 1 and parent.parts[1].startswith('data')) |
| `code/sj/orch_cd/evalx/work/milestone/stdout_transfer.py` | 93 | error branch with condition | path.exists() or path.is_symlink() |
| `code/sj/orch_cd/evalx/work/milestone/stdout_transfer.py` | 105 | error branch with condition | len(line) > LINE_LIMIT |
| `code/sj/orch_cd/evalx/work/milestone/stdout_transfer.py` | 108 | error branch with condition | protocol and (ended or not line.endswith(b'\n')) |
| `code/sj/orch_cd/evalx/work/milestone/stdout_transfer.py` | 111 | error branch with condition | header is not None |
| `code/sj/orch_cd/evalx/work/milestone/stdout_transfer.py` | 114 | error branch with condition | not isinstance(header, dict) |
| `code/sj/orch_cd/evalx/work/milestone/stdout_transfer.py` | 119 | error branch with condition | stream is None |
| `code/sj/orch_cd/evalx/work/milestone/stdout_transfer.py` | 122 | error branch with condition | not raw or len(raw) > CHUNK or received + len(raw) > header['bytes'] |
| `code/sj/orch_cd/evalx/work/milestone/stdout_transfer.py` | 130 | error branch with condition | header is None or received != header['bytes'] or hashed.hexdigest() != header['sha256'] or (line[len(END):-1].decode('ascii') != header['sha256']) |
| `code/sj/orch_cd/evalx/work/milestone/stdout_transfer.py` | 137 | error branch with condition | logged > LOG_LIMIT |
| `code/sj/orch_cd/evalx/work/milestone/stdout_transfer.py` | 141 | error branch with condition | not ended |
| `code/venue.py` | 17-20,49,51-54,105,108-109,118-120,123-126,128-130,132-134,136-143,145,173-187,189-190 | UNEXPLAINED | No test or rehearsal executed this job-source line. |
| `code/venue.py` | 50 | error branch with condition | source.stat().st_size > budget |
| `code/venue.py` | 188 | error branch with condition | plan['missing'] |

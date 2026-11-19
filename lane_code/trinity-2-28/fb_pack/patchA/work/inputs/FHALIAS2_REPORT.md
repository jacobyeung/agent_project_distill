Integration-ready for review: six-file patch; 127 focused tests and the host regression pass on both copies. A new tree seal is required.
`student_pilot/job_env.py:4`: adds Q_E7; `key()` is unchanged. Boundary tests cover native fallback and alias precedence.
`student_pilot/r2_intake.py:10,39` and `r2_materialize.py:5,26`: resolve the host flag through env_key; boundary tests preserve limits and local/Trinity vetoes.
`launch_r2/runtime.py:61–66`: matches the exact env_key lookup and requires exactly one intake guard; five execution receipts remain unchanged in shape.
Runtime mutations remove or duplicate each guard: materializer refuses on both copies; intake refuses after. `bash work/run.sh work/check_missing_intake_tree.py work/tree_LABEL LABEL2` verifies an actual mutated tree (accepted before, refused after).
`launch_r2/host.py:253`: clears inherited Q_E7 before checks/scene preparation, preserving native zero/one writes; host regressions test inherited 0 and 1.
`launch_r2/distributed.py:77`: clears Q_E7 before K6 translation; 27 environment combinations preserve legacy native behavior, including absent K6.
`rg -n -m 12 "STUDENT_R2_FRAME_HOST|Q_E7|Statement obligation|getsourcelines|inspect.getsource" work/tree_before -g "*.py"` locates consumers; source_matches.txt records them. No other frame-host text matcher exists.
Commands below run from this workspace through run.sh (nice 10, eight CPU threads, offline, CUDA hidden). LABEL means before or after.
`bash work/run.sh work/check_boundary2.py work/tree_LABEL LABEL2_contract`: 5/5 pass per copy; expectations encode each copy’s contract.
`bash work/run.sh work/compare_boundary2.py`: 12 changed subcases across intake/materialization; scanner admits Q_E7 and rejects the native-name literal on both.
`bash work/run.sh work/run_focused_exact.py work/tree_LABEL LABEL2 main`: 112/112 each; `bash work/run.sh work/run_focused.py work/tree_LABEL LABEL2 GROUP`: edges 4/4 and producer 11/11 each.
`bash work/run.sh work/run_host_regression.py work/tree_LABEL LABEL2_final host`: 1/1 each; test_native_prepare_and_every_rank_encode passes.
`bash work/run.sh work/run_host_regression.py work/tree_before before2_final_checks integration` and `... work/tree_after after2_checks integration`: 12/12 each, including runtime containment and source mutations.
Full-host mutation tests execute the actual host AST statements with the real materializer; worker tests stop before source verification/training. These tests do not admit production.
`bash work/run.sh work/check_static2.py`: only intended lines change; `bash work/run.sh work/seal_patch2.py`: 936-file inventories, source==before, six changed files and SHA-256 values below.
`patch --dry-run -p1 -d work/tree_before < out/ALIAS.patch` passes. `bash work/run.sh work/finalize2.py` verifies counts and matching focused outcomes.
`launch_r2/distributed.py`: 9fec5743ecf8b69c74a7c9debc0fa610ccda182397959eed21d87a05642cc01d -> fa4221a306269a38e04d1b844ec78d60cc11778d85f4177d58d6e8471ca17d91
`launch_r2/host.py`: 3ca2cdff76593a50b3d78ce4ccfbbaa09ea6349f4320fea9be5a8dd297a8a843 -> 3587742802c7cb14f39aa0c4feb94cbd6cadaba6fc9e5c5f43655215d5185bed
`launch_r2/runtime.py`: e23656c8f3016a32bae1d0322f43fad67f6207a62c554af94a92f979091d76f1 -> 5be49d551a9bf94887fb9b7c20a3b338fe76658b377ad30321e6407e8fadf7b7
`student_pilot/job_env.py`: 05def1cad6ccf0adcfa678982d701a9378a3e5615b7ccf5df08aa617f57a03b3 -> 217ff0c7b8a6ea721ae1e833e21421e98b581e0c8e56708f64e4f78ae6459a88
`student_pilot/r2_intake.py`: fc968e85827dc56686c6b11814a02b3274f52fb3ca6281758111e1612a3e1c48 -> 2e96e97d9306f3d08c56cc3e189a8b0fcc5a9462bee68a168f451df52448bbb1
`student_pilot/r2_materialize.py`: 47a362bb95cfafcd0b007fd955eb5990d7755ebabd2615d91a9fafe5c47bf0a3 -> 0c2a7bc1b140571dfb6ed9a27a909f00c09c852413ec3c09d6c5cfa5cc499f98
Remaining risks: exact source-text checks retain formatting sensitivity; intake validation does not add an execution receipt. Legacy P paths intentionally ignore inherited Q_E7.
Empty envelopes/synthetic RGB establish boundaries and CPU encoding only; production data, full producer success, kit resealing and launch admission remain unverified.
Reproduction uses existing w21 fixtures listed by exact path/hash in evidence JSON. Native fixture JSON retains its schema; all review JSON records input_sha256.
`bash work/package2.sh` creates out/sb_fhalias2.tar and its SHA-256 sidecar; `bash work/run.sh work/verify_archive2.py` verifies archived bytes, hashes and report length.
The source lane is read-only and unchanged. No GPU, network, SSH, tmux, Git, process termination or deletion was used.
6c5e42942c6b7453613d551142c8ed0deb059a750a91ebd83a41a7e7539fd459  out/sb_fhalias2.tar

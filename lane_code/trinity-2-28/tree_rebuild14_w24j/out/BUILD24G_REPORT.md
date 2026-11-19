BUILD24G PASS. The kit-only copier fix is packaged; normal kits remain GO=false.
Tree: 57a1f14df5ab60e5783a4baa76e714476770d2bd29f5d98c514a14be6412c6f7; all 939 files are byte-identical to build 24f (work/build24g/INVARIANTS.json).
Kit n: 97b8b2b7da50070db82efa90c8ec3052827d0555f6780b8067dbfc1f88f2cad2; kit q: 3d14429690aae6ebd1dc569010802487d37944368a4e6b78a9e016b69717d6a8.
GO variant: 041ea3e23065f68fe7d1acbb9aed6a7af4cce84dc9650009b1e545fe703dacc7; it is not authorized for upload.
Kit n and kit_n_go run the copier. Kit q has no copier; resealing it preserves its seal and bytes.
Default sessions file: /project/community/jjyeung/okh7/x_22c714e1/n_s/sess.json; k/p.json supplies n_root, independently of the live-output target.
TK_KIT_HOME is ignored. --sessions PATH selects an explicit file; the existing explicit home API remains supported.
The directory must be owned by the job user with mode 0700. The file must be regular, non-symlink, mode 0600, and a JSON object mapping part names to HTTP(S) URLs.
Opened directory/file descriptors prevent symlink replacement; validation failures use fixed reason text and upload nothing.
The private node-local directory/file use 0700/0600. Writer stdout and stderr are discarded; no session value enters live evidence or reports.
Copier evidence: five failing-before controls, thirteen passing-after cases, and an explicit CLI success (work/build24g/COPIER_TESTS.json).
Late mint, writer failure redaction, complete four-part mapping, directory symlink and missing-directory tests pass (EXTRA_COPIER_TESTS.json).
Decoded q/n/GO scans and kit, naming, resolver and guard suites pass (work/build24g/SCAN_*.json, SUITES.json and VALIDATION.json).
Live-copy tests pass, including TERM, byte cap, idempotence, stop generations and checkpoint fallback; runtime tests pass (LIVE_TESTS.json and RUNTIME_TESTS.json).
SESSION_NAMES_24F.json is byte-identical; no SESSION_NAMES_24G.json is needed. The card supplies the authoritative sessions location and modes.
Upload delta after 24f: 3 files, 20727 bytes; stream root work/build24g/upload; out/UPLOADS_24G.list names the files.
out/UPLOADS_24G_GO.json contains only the three-file GO delta against kit n and is not authorized for upload.
The tree, configs, admission, legality, removals, opener rows, step-544 lineage, resolver identity checks and DEFERRED boundary remain unchanged.
Existing packages remain unchanged. No rehearsal path was opened or modified, and go_rehearsal.sh was not run; no distributed result is claimed.
out/DELIVERY_24G.json records the package path, SHA-256, bytes and verified member seal. Evidence paths without a prefix are under work/build24g.

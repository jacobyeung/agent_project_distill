{
  "schema": "orchkit-verdict-v1",
  "utc": "2026-11-16T13:27:49Z",
  "reviewer_lane": "codex_review_orchkit_core_2",
  "kit_pins_sha256": null,
  "verdict": "NO_GO",
  "scope_files": [
    "tools/orchkit/anon.py",
    "tools/orchkit/ANON_WORDS.txt",
    "tools/orchkit/launch.py",
    "tools/orchkit/templates/job.sh.tmpl",
    "tools/orchkit/schema/config.schema.json",
    "tools/orchkit/pack.py",
    "tools/orchkit/util.py",
    "tools/orchkit/examples/read_step.config.json",
    "tools/orchkit/tests"
  ],
  "validation": {
    "method": "Read-only reproductions with in-memory fixtures and mocked side effects. OC-06 through OC-08 use mocks adapted to the new allocation and exclusive-intent operations.",
    "unit_test_output": "Ran 1 test in 0.003s\nOK",
    "full_suite": "Not run: the suite requires filesystem writes and includes reads outside the permitted scope.",
    "baseline_comparison": "Reconstructed the pre-fix anon.py in memory by reversing its hunks from FIX_1.diff; verified every hunk against the current source."
  },
  "findings": [
    {
      "id": "OC-01",
      "text": {
        "status": "fixed",
        "detail": "All five original fixtures now produce opacity hits or fail closed."
      },
      "output": [
        "disguised_gzip [{'where': 'a.bin!gz', 'scope': 'text', 'rule': 'rule 19'}, {'where': 'a.bin!gz!/x', 'scope': 'text', 'rule': 'rule 19'}]",
        "depth_five [{'where': 'a.tgz!gz!/a.tgz!gz!/a.tgz!gz!/a.tgz!gz!/a.tgz', 'scope': 'size', 'rule': 'too-deep'}]",
        "tar_uname [{'where': 'a.tar', 'scope': 'text', 'rule': 'rule 19'}, {'where': 'a.tar!/x', 'scope': 'name', 'rule': 'rule 19'}]",
        "fifo_bytes [{'where': 'a.tar', 'scope': 'text', 'rule': 'rule 19'}, {'where': 'a.tar!/x', 'scope': 'size', 'rule': 'special'}]",
        "utf16 [{'where': 'a.txt', 'scope': 'text', 'rule': 'rule 19'}]"
      ]
    },
    {
      "id": "OC-02",
      "text": {
        "status": "fixed",
        "detail": "The original reproduction still returns empty results from its old text-only calls. Current prepare uses additional checks. Running prepare separately with each forbidden root, environment, and pool fixture rejects all three at the CONFIG.json opacity check; unrelated pin checks were mocked."
      },
      "output": [
        "Original reproduction: schema []; config_hits []; batch_hits []; submit_hits []; actual_env_hits 2",
        "root opacity: [{\"rule\": \"rule 7\", \"scope\": \"name\", \"where\": \"CONFIG.json\"}]",
        "env opacity: [{\"rule\": \"rule 7\", \"scope\": \"name\", \"where\": \"CONFIG.json\"}]",
        "pool opacity: [{\"rule\": \"rule 7\", \"scope\": \"name\", \"where\": \"CONFIG.json\"}]",
        "OC-02 current_env_hits 2",
        "OC-02 current_batch_name_hits [{'where': 'script', 'scope': 'name', 'rule': 'rule 7'}]",
        "OC-02 current_submit_name_hits [{'where': 'submit', 'scope': 'name', 'rule': 'rule 7'}]"
      ]
    },
    {
      "id": "OC-03",
      "text": {
        "status": "fixed",
        "detail": "Both original forbidden strings are detected."
      },
      "output": [
        "ORCH_N30 [{'where': 'x', 'scope': 'text', 'rule': 'rule 29'}]",
        "orchkit-pins-v1-private [{'where': 'x', 'scope': 'text', 'rule': 'rule 39'}]"
      ]
    },
    {
      "id": "OC-04",
      "text": {
        "status": "fixed",
        "detail": "mint_job_name rejects the original token containing a trailing newline."
      },
      "output": [
        "LaunchError: token must be 16 lowercase hex: '0123456789abcdef\\n'"
      ]
    },
    {
      "id": "OC-05",
      "text": {
        "status": "fixed",
        "detail": "A failing mocked squeue stops the generated gate before WOULD_SUBMIT."
      },
      "output": [
        "rc=6 stdout=LIVE unknown: squeue failed"
      ]
    },
    {
      "id": "OC-06",
      "text": {
        "status": "fixed",
        "detail": "The generated check requests the full 100 MiB allocation. A mocked 16 MiB remaining quota causes refusal. All filesystem operations were mocked."
      },
      "output": [
        "SHORT home [Errno 122] Disk quota exceeded",
        "OC-06 required=104857600 quota_remaining=16777216 requested=[104857600] exit=3 accepted=False"
      ]
    },
    {
      "id": "OC-07",
      "text": {
        "status": "fixed",
        "detail": "The deterministic interleaving now occurs immediately before the exclusive intent creation. One caller acquires the intent; the other is rejected. Only one reaches mocked transport."
      },
      "output": [
        "race transport_calls_same_token 1 altered_bytes_sent False approved_bytes_sent True errors ['submission UNCERTAIN: ', 'another submit of 0123456789abcdef holds the intent; never repeat a submit']"
      ]
    },
    {
      "id": "OC-08",
      "text": {
        "status": "fixed",
        "detail": "Replacing SUBMIT.sh at intent creation sends the previously verified bytes. Replacing it immediately after _load_prep causes refusal before transport. Both cases use actual _load_prep hashing over in-memory files."
      },
      "output": [
        "swap_at_intent transport_calls_same_token 1 altered_bytes_sent False approved_bytes_sent True errors ['submission UNCERTAIN: ']",
        "swap_after_load transport_calls_same_token 0 altered_bytes_sent False approved_bytes_sent False errors ['SUBMIT.sh changed after prepare']"
      ]
    },
    {
      "id": "OC-09",
      "severity": "blocker",
      "class": "legality",
      "file": "tools/orchkit/anon.py",
      "line_start": 149,
      "line_end": 162,
      "text": {
        "status": "not fixed",
        "detail": "The new compression branch scans only decompressed bytes and discards the original representation. It therefore misses qwen in a gzip filename header and in trailing bytes after bz2 or xz streams. All three fixtures were rejected by the pre-fix scanner and are accepted now. prepare uses this scanner, while bundle_bytes preserves the original file bytes, so forbidden content can pass opacity checks and ship unchanged."
      },
      "repro": [
        "env",
        "TMPDIR=/scratch/jjyeung/orch_n30/e_orchkit-core/tmp",
        "PYTHONPATH=/scratch/jjyeung/orch_n30/e_orchkit-core/repo/tools",
        "/usr/bin/python3",
        "-B",
        "-c",
        "import io,gzip,bz2,lzma\nfrom unittest.mock import patch\nfrom orchkit import anon\nrules=anon.load_rules()\nbuf=io.BytesIO()\nwith gzip.GzipFile(filename='qwen.txt',fileobj=buf,mode='wb',mtime=0) as f:f.write(b'ok')\nfor label,data in [('gzip_filename',buf.getvalue()),('bz2_trailer',bz2.compress(b'ok')+b'qwen'),('xz_trailer',lzma.compress(b'ok')+b'qwen')]:\n with patch('os.path.isfile',return_value=True),patch('os.path.islink',return_value=False),patch('os.path.getsize',return_value=len(data)),patch('builtins.open',side_effect=lambda *a,**k:io.BytesIO(data)):\n  print(label,anon.scan_tree('a.bin',rules))\n"
      ],
      "output": [
        "gzip_filename []",
        "bz2_trailer []",
        "xz_trailer []"
      ],
      "baseline_output": [
        "gzip_filename before=[{'where': 'a.bin', 'scope': 'text', 'rule': 'rule 19'}] after=[]",
        "bz2_trailer before=[{'where': 'a.bin', 'scope': 'text', 'rule': 'rule 19'}] after=[]",
        "xz_trailer before=[{'where': 'a.bin', 'scope': 'text', 'rule': 'rule 19'}] after=[]"
      ],
      "expect": "Each fixture must produce an opacity hit or fail closed."
    }
  ]
}

OC-01 through OC-08 pass their reproductions.
OC-09 introduces a verified opacity bypass; the verdict remains NO_GO.
The job-name unit test passed. The full suite was not run.
No files were changed, and no Git, SSH, scheduler, or network commands ran.
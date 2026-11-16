{
  "schema": "orchkit-verdict-v1",
  "utc": "2026-11-16T13:34:40Z",
  "reviewer_lane": "codex_review_orchkit_core_3",
  "kit_pins_sha256": null,
  "verdict": "NO_GO",
  "scope_files": [
    "tools/orchkit/anon.py",
    "tools/orchkit/ANON_WORDS.txt",
    "tools/orchkit/launch.py",
    "tools/orchkit/pins.py",
    "tools/orchkit/pack.py",
    "tools/orchkit/util.py",
    "tools/orchkit/templates/job.sh.tmpl",
    "tools/orchkit/schema/config.schema.json",
    "tools/orchkit/examples/read_step.config.json",
    "tools/orchkit/tests"
  ],
  "validation": {
    "method": "Read-only reproductions with in-memory fixtures and mocked filesystem mutations and transport. OC-02 additionally exercises current prepare. OC-06 through OC-08 use mocks adapted to the allocation, exclusive-intent and pinned-byte operations.",
    "unit_test_output": "Ran 1 test in 0.004s\nOK",
    "full_suite": "Not run: the filesystem is read-only, and template tests can read fixtures outside the permitted scope.",
    "baseline_comparison": "Reconstructed pre-fix anon.py in memory by reversing FIX_2.diff and FIX_1.diff, asserting that every replacement matched exactly once.",
    "side_effects": "No files changed. No Git, SSH, Slurm or network commands ran. The squeue reproduction used a local shell function."
  },
  "findings": [
    {
      "id": "OC-01",
      "text": {
        "status": "fixed",
        "detail": "All five original fixtures produce opacity hits or fail closed."
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
        "detail": "The original text-only calls still return empty results. Current prepare rejects each forbidden root, environment and pool fixture through the CONFIG.json name scan. Unrelated pin checks were mocked."
      },
      "output": [
        "Original reproduction: schema []; config_hits []; batch_hits []; submit_hits []; actual_env_hits 2",
        "root opacity: [{\"rule\": \"rule 7\", \"scope\": \"name\", \"where\": \"CONFIG.json\"}]",
        "env opacity: [{\"rule\": \"rule 7\", \"scope\": \"name\", \"where\": \"CONFIG.json\"}]",
        "pool opacity: [{\"rule\": \"rule 7\", \"scope\": \"name\", \"where\": \"CONFIG.json\"}]"
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
        "detail": "mint_job_name rejects the token containing a trailing newline."
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
        "detail": "The room check requests the full 100 MiB allocation and refuses the simulated 16 MiB quota."
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
        "detail": "The deterministic interleaving at exclusive intent creation permits only one caller to reach transport."
      },
      "output": [
        "race transport_calls_same_token 1 altered_bytes_sent False approved_bytes_sent True errors ['submission UNCERTAIN: ', 'another submit of 0123456789abcdef holds the intent; never repeat a submit']"
      ]
    },
    {
      "id": "OC-08",
      "text": {
        "status": "fixed",
        "detail": "A replacement at intent creation does not change the verified bytes sent. A replacement immediately after _load_prep causes refusal before transport."
      },
      "output": [
        "swap_at_intent transport_calls_same_token 1 altered_bytes_sent False approved_bytes_sent True errors ['submission UNCERTAIN: ']",
        "swap_after_load transport_calls_same_token 0 altered_bytes_sent False approved_bytes_sent False errors ['SUBMIT.sh changed after prepare']"
      ]
    },
    {
      "id": "OC-09",
      "text": {
        "status": "fixed",
        "detail": "The gzip filename and both compressed-stream trailers now produce opacity hits. The bz2 and xz trailers also fail decoding checks."
      },
      "output": [
        "gzip_filename [{'where': 'a.bin', 'scope': 'text', 'rule': 'rule 19'}]",
        "bz2_trailer [{'where': 'a.bin', 'scope': 'text', 'rule': 'rule 19'}, {'where': 'a.bin', 'scope': 'size', 'rule': 'undecodable'}]",
        "xz_trailer [{'where': 'a.bin', 'scope': 'text', 'rule': 'rule 19'}, {'where': 'a.bin', 'scope': 'size', 'rule': 'undecodable'}]"
      ]
    },
    {
      "id": "OC-10",
      "severity": "blocker",
      "class": "admission",
      "file": "tools/orchkit/anon.py",
      "line_start": 220,
      "line_end": 227,
      "text": {
        "status": "not fixed",
        "detail": "FIX_1 makes compressed files expand into archive and decompressed rows, but walk_blobs discards archive rows. Consequently pins.check_single_place no longer sees hashes in the original compression header. A gzip file named a.bin whose filename header contains another pinned file's SHA-256 was rejected before FIX_1 and now passes. FIX_2 restores these bytes to scan_tree but not to walk_blobs. Current prepare accepts the fixture, and bundle_bytes preserves the duplicate hash in the shipped header."
      },
      "repro": [
        "env",
        "TMPDIR=/scratch/jjyeung/orch_n30/e_orchkit-core/tmp",
        "PYTHONPATH=/scratch/jjyeung/orch_n30/e_orchkit-core/repo/tools",
        "/usr/bin/python3",
        "-B",
        "-c",
        "import io,gzip,os\nfrom unittest.mock import patch\nfrom orchkit import anon,pins,util\nrules=anon.load_rules()\ndigest=util.sha256_bytes(b'ok');buf=io.BytesIO()\nwith gzip.GzipFile(filename=digest,fileobj=buf,mode='wb',mtime=0) as f:f.write(b'clean')\nfiles={'a.bin':buf.getvalue(),'data.bin':b'ok'}\nmanifest={'schema':'orchkit-pins-v1','created_utc':'2026-11-16T00:00:00Z','commit':None,'source_seal':None,'entries':[{'role':'input','logical_path':name,'bytes':len(data),'sha256':util.sha256_bytes(data),'source':{'kind':'file','uri':name,'generation':None}} for name,data in sorted(files.items())]}\nfiles['PINS.json']=util.canonical_json(manifest)\nwith patch('builtins.open',side_effect=lambda p,*a,**k:io.BytesIO(files[os.path.basename(p)])),patch('os.path.isfile',side_effect=lambda p:os.path.basename(p) in files),patch('os.path.islink',return_value=False),patch('os.path.getsize',side_effect=lambda p:len(files[os.path.basename(p)])),patch('os.walk',return_value=[('/virtual',[],list(files))]):\n print('after','opacity_hits',anon.scan_tree('/virtual',rules))\n print('after','single_place',pins.check_single_place('/virtual'))\n"
      ],
      "output": [
        "after opacity_hits []",
        "after single_place []"
      ],
      "baseline_output": [
        "before opacity_hits []",
        "before single_place [{'where': 'a.bin', 'field': None, 'value': '2689367b205c16ce32ed4200942b8b8b1e262dfc70d9bc9fbc77c49699a4f1df', 'reason': 'copy of a pinned hash outside PINS.json'}]"
      ],
      "prepare_validation": {
        "method": "Added a schema-valid CONFIG.json to the same in-memory kit and ran actual prepare, pin verification, single-place checking, opacity checking and bundling. Provenance and filesystem writes were mocked. Swapping only pins.walk_blobs between the reconstructed baseline and current implementation changes refusal to acceptance.",
        "output": [
          "before prepare REFUSED single-place invariant: [{\"field\": null, \"reason\": \"copy of a pinned hash outside PINS.json\", \"value\": \"2689367b205c16ce32ed4200942b8b8b1e262dfc70d9bc9fbc77c49699a4f1df\", \"where\": \"a.bin\"}]",
          "after prepare ACCEPTED",
          "bundled_header_hash_preserved True"
        ]
      },
      "expect": "The single-place check must reject the duplicate pinned hash before prepare succeeds."
    }
  ]
}

OC-01 through OC-09 pass their reproductions.
OC-10 introduces a verified bypass of prepare’s single-place invariant; the verdict remains NO_GO.
The job-name unit test passed. The full suite was not run.
No files changed, and no Git, SSH, Slurm or network commands ran.
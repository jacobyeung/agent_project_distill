{
  "schema": "orchkit-verdict-v1",
  "reviewer_lane": "codex_review_orchkit_core_10",
  "requested_head": "633e3d0b",
  "kit_pins_sha256": null,
  "verdict": "NO_GO",
  "validation": {
    "method": "Reran all 30 requested reproductions using in-memory filesystem fixtures and mocked transport. Adapted earlier fixtures for current snapshots, locks, minted payload identities and build_submission's return value.",
    "status_scope": "fixed means the original reproduced input now meets the specification. Additional bypasses are reported separately.",
    "unit_test_output": "Ran 1 test in 0.003s\nOK",
    "full_suite": "Not run because this session's filesystem is read-only. The job-name test and in-memory reproductions ran.",
    "controls": [
      "NO_GO and GO naming another token: refused with zero transport calls.",
      "GO naming the correct job: accepted with one mocked transport call.",
      "Remote live gate: empty queue accepted; existing job refused; correctly named QUEUE_BEHIND accepted; wrong QUEUE_BEHIND refused.",
      "Home quota shortage refused after attempting the full allocation. Pool quota shortage refused after a successful home check."
    ],
    "side_effects": "No files changed. No Git, SSH, Slurm or network commands ran. Remote live-gate tests used a local shell function. No jobs were submitted."
  },
  "findings": [
    {
      "id": "OC-01",
      "text": {
        "status": "fixed",
        "detail": "All five original container and encoding fixtures are detected or refused."
      },
      "output": "disguised_gzip: rule 19; depth_five: too-deep; tar_uname: rule 19; fifo_bytes: rule 19 and special; utf16: rule 19"
    },
    {
      "id": "OC-02",
      "text": {
        "status": "fixed",
        "detail": "Preparation refuses each original root, environment and pool fixture."
      },
      "output": "root, env, pool: REFUSED CONFIG.json opacity rule 7"
    },
    {
      "id": "OC-03",
      "text": {
        "status": "fixed",
        "detail": "Both original naming bypasses are detected."
      },
      "output": "ORCH_N30: rule 29; orchkit-pins-v1-private: rule 39"
    },
    {
      "id": "OC-04",
      "text": {
        "status": "fixed",
        "detail": "The trailing-newline token is refused. The job-name unit test passes."
      },
      "output": "REFUSED token must be 16 lowercase hex: '0123456789abcdef\\n'"
    },
    {
      "id": "OC-05",
      "text": {
        "status": "fixed",
        "detail": "A failed scheduler query stops the remote gate."
      },
      "output": "rc=6 stdout=LIVE unknown: squeue failed"
    },
    {
      "id": "OC-06",
      "text": {
        "status": "fixed",
        "detail": "The room check attempts the entire budget and refuses the simulated quota shortage."
      },
      "output": "SHORT home [Errno 122] Disk quota exceeded; exit 3; allocated [104857600]"
    },
    {
      "id": "OC-07",
      "text": {
        "status": "fixed",
        "detail": "Interleaving a second submission immediately before intent creation permits only one transport call."
      },
      "output": "nested: REFUSED another submission to this partition is in progress; first: SUBMITTED; calls 1"
    },
    {
      "id": "OC-08",
      "text": {
        "status": "fixed",
        "detail": "Replacing SUBMIT.sh after loading causes refusal. Replacing it at intent creation cannot alter the rebuilt bytes sent."
      },
      "output": "after_load: REFUSED, calls 0; at_intent: SUBMITTED, calls 1; altered_sent False"
    },
    {
      "id": "OC-09",
      "text": {
        "status": "fixed",
        "detail": "The original forbidden gzip filename and bz2/xz trailers are detected."
      },
      "output": "gzip_filename: rule 19; bz2_trailer and xz_trailer: rule 19 and undecodable"
    },
    {
      "id": "OC-10",
      "text": {
        "status": "fixed",
        "detail": "The pinned hash copied into a compression header violates the single-place check."
      },
      "output": "a.bin and a.bin!gzip-header: copy of a pinned hash outside PINS.json"
    },
    {
      "id": "OC-11",
      "text": {
        "status": "fixed",
        "detail": "Changing the source kit during provenance leaves the checked snapshot unchanged."
      },
      "output": "SUBMITTED transport_calls 1 shipped_data b'ok'"
    },
    {
      "id": "OC-12",
      "text": {
        "status": "fixed",
        "detail": "The original token-only metadata substitution is refused."
      },
      "output": "REFUSED the prepared scripts do not belong to token fedcba9876543210; calls 0"
    },
    {
      "id": "OC-13",
      "text": {
        "status": "fixed",
        "detail": "Both ordinary and prefixed ZIP fixtures are inspected and refused."
      },
      "output": "Both fixtures: a.zip!/x rule 19; prepare REFUSED opacity"
    },
    {
      "id": "OC-14",
      "text": {
        "status": "fixed",
        "detail": "Duplicate-key values, root strings and UTF-16 copies of pinned hashes are detected."
      },
      "output": "duplicate_key, root_string, utf16: prepare REFUSED single-place invariant"
    },
    {
      "id": "OC-15",
      "text": {
        "status": "fixed",
        "detail": "An appended empty ZIP no longer hides the tar interpretation."
      },
      "output": "opacity fixture: REFUSED rule 19 at a.bin!/x.gz!gz; hash fixture: REFUSED single-place invariant"
    },
    {
      "id": "OC-16",
      "text": {
        "status": "fixed",
        "detail": "Both original submission-script and transport-argument substitutions are refused."
      },
      "output": "script: SUBMIT.sh differs from its rebuild; argv: transport command differs; calls 0 for both"
    },
    {
      "id": "OC-17",
      "text": {
        "status": "fixed",
        "detail": "The forbidden path in the discarded duplicate CONFIG.json value is detected."
      },
      "output": "REFUSED CONFIG.json opacity rule 7"
    },
    {
      "id": "OC-18",
      "text": {
        "status": "fixed",
        "detail": "All four original Unicode-escape representations are detected."
      },
      "output": "utf16, utf32, gzip_json, json_without_extension: prepare REFUSED opacity rule 19"
    },
    {
      "id": "OC-19",
      "text": {
        "status": "fixed",
        "detail": "The original truncated ZIP is refused."
      },
      "output": "Python: BadZipFile; scanner: unsupported-container; prepare REFUSED unscannable"
    },
    {
      "id": "OC-20",
      "text": {
        "status": "fixed",
        "detail": "Changing PREP/kit/data.bin at the JOB.json read fails submission-snapshot validation."
      },
      "output": "REFUSED pins differ: actual bytes 4, expected bytes 2; calls 0"
    },
    {
      "id": "OC-21",
      "text": {
        "status": "fixed",
        "detail": "Two preparation copies reach transport only once. A separate direct check confirms that the shared token claim refuses reuse."
      },
      "output": "transport_calls_same_token 1; ledger_submitted_rows 1; second claim REFUSED token 0123456789abcdef was already claimed"
    },
    {
      "id": "OC-22",
      "text": {
        "status": "fixed",
        "detail": "Mutating partition metadata causes refusal. The unchanged concurrent-submission control permits one transport call."
      },
      "output": "control: calls 1, outcomes ['REFUSED', 'SUBMITTED']; mutation: REFUSED partition differs between config, ledger and SUBMIT.json"
    },
    {
      "id": "OC-23",
      "text": {
        "status": "fixed",
        "detail": "The original octal, named-character and JSON slash escapes are detected."
      },
      "output": "octal.py and named.py: REFUSED rule 19; escaped slash: REFUSED rule 24"
    },
    {
      "id": "OC-24",
      "text": {
        "status": "fixed",
        "detail": "Both original damaged-container fixtures are refused."
      },
      "output": "prefixed ZIP and bad-checksum tar: unsupported-container; prepare REFUSED unscannable"
    },
    {
      "id": "OC-25",
      "text": {
        "status": "resolved_by_specification",
        "detail": "The clarified rule permits split in ordinary file contents. The earlier finding remains withdrawn."
      }
    },
    {
      "id": "OC-26",
      "text": {
        "status": "fixed",
        "detail": "Changing JOB.json sessions or adding an unminted DRYRUN_REPORT.json fails the whole-bundle payload comparison."
      },
      "output": "JOB and DRYRUN: REFUSED payload differs from the one its ledger row names; calls 0 for both"
    },
    {
      "id": "OC-27",
      "text": {
        "status": "fixed",
        "detail": "The original backslash-LF continuation is detected. OC-35 reports the CR variant."
      },
      "output": "line_continuation: prepare REFUSED a.py opacity rule 19"
    },
    {
      "id": "OC-28",
      "text": {
        "status": "fixed",
        "detail": "The original gzip filename receives name checks. OC-32 reports the concatenated-member variant."
      },
      "output": "gzip_fname: prepare REFUSED a.gz!gzip-header name rule 7"
    },
    {
      "id": "OC-29",
      "text": {
        "status": "fixed",
        "detail": "The original damaged tar with a UTF-8 filename is refused."
      },
      "output": "Python: ReadError bad checksum; prepare REFUSED unscannable (unsupported-container)"
    },
    {
      "id": "OC-30",
      "text": {
        "status": "fixed",
        "detail": "The original default LZMA-alone stream is inspected. OC-33 reports nondefault standard settings."
      },
      "output": "lzma_alone: prepare REFUSED a.lzma!lzma opacity rule 19"
    },
    {
      "id": "OC-31",
      "text": {
        "status": "fixed",
        "detail": "Both the bare mount root and redundant leading slash are refused. OC-36 reports dot-component variants."
      },
      "output": "/data2 and //data2/secret: prepare REFUSED CONFIG.json opacity rule 24"
    },
    {
      "id": "OC-32",
      "severity": "blocker",
      "class": "legality",
      "file": "tools/orchkit/anon.py",
      "line_start": 277,
      "line_end": 287,
      "text": {
        "status": "not fixed",
        "detail": "Only the first gzip member's filename receives name checks. Python reads concatenated gzip members, but a later member's stored filename split.txt passes scanning and preparation unchanged."
      },
      "repro_python": "raw=io.BytesIO()\nwith gzip.GzipFile(filename='split.txt',fileobj=raw,mode='wb',mtime=0) as f:f.write(b'ok')\nblob=gzip.compress(b'first')+raw.getvalue()\nconfirm('concat_gzip_fname','a.gz',blob,gzip.decompress(blob))",
      "output": "concat_gzip_fname hits [] prepare ACCEPTED unchanged True decoded b'firstok'",
      "expect": "Apply filename checks to every gzip member or refuse concatenated streams."
    },
    {
      "id": "OC-33",
      "severity": "blocker",
      "class": "legality",
      "file": "tools/orchkit/anon.py",
      "line_start": 170,
      "line_end": 171,
      "text": {
        "status": "not fixed",
        "detail": "LZMA-alone recognition requires the default property byte 0x5d. Python's standard compressor produces readable streams with other property bytes. Streams containing qwen with lc=0, 1, 2 or 4 all pass preparation unchanged."
      },
      "repro_python": "import lzma\nblob=lzma.compress(b'qwen',format=lzma.FORMAT_ALONE,filters=[{'id':lzma.FILTER_LZMA1,'lc':0}])\nconfirm('lzma_lc0','a.lzma',blob,lzma.decompress(blob))",
      "output": "lzma_lc0 hits [] prepare ACCEPTED unchanged True decoded b'qwen'",
      "expect": "Inspect standard LZMA-alone property combinations or refuse them."
    },
    {
      "id": "OC-34",
      "severity": "blocker",
      "class": "legality",
      "file": "tools/orchkit/anon.py",
      "line_start": 172,
      "line_end": 174,
      "text": {
        "status": "not fixed",
        "detail": "Zlib recognition requires the default 0x78 header byte. Standard streams produced with smaller window sizes bypass inspection. Streams containing qwen with wbits=9, 10 or 14 all pass preparation unchanged; the wbits=15 control is refused."
      },
      "repro_python": "import zlib\ne=zlib.compressobj(wbits=9)\nblob=e.compress(b'qwen')+e.flush()\nconfirm('zlib_wbits9','a.zlib',blob,zlib.decompress(blob))",
      "output": "zlib_wbits9 hits [] prepare ACCEPTED unchanged True decoded b'qwen'",
      "expect": "Inspect all standard zlib window sizes or refuse them."
    },
    {
      "id": "OC-35",
      "severity": "blocker",
      "class": "legality",
      "file": "tools/orchkit/anon.py",
      "line_start": 99,
      "line_end": 100,
      "text": {
        "status": "not fixed",
        "detail": "The continuation fix handles LF and CRLF but misses CR line endings. Python interprets backslash-CR as a continuation, decoding the fixture to qwen. The scanner leaves the CR between the letters, and preparation accepts the source unchanged."
      },
      "repro_python": "blob=b'x = \"q'+bytes([92,13])+b'wen\"\\n'\nconfirm('cr_continuation','a.py',blob,ast.literal_eval(blob.decode().partition('=')[2].strip()))",
      "output": "cr_continuation hits [] prepare ACCEPTED unchanged True decoded 'qwen'",
      "expect": "Handle Python's CR line endings when decoding continuations."
    },
    {
      "id": "OC-36",
      "severity": "blocker",
      "class": "legality",
      "file": "tools/orchkit/ANON_WORDS.txt",
      "line_start": 23,
      "line_end": 25,
      "text": {
        "status": "not fixed",
        "detail": "Ordinary dot components bypass the cluster-path rules. All four reproduced root_parent values pass schema validation, scanning and preparation even though lexical normalization yields a prohibited cluster path. These values enter CONFIG.json and the rendered batch script."
      },
      "repro_python": "for path in ['/./data2/secret','/tmp/../data2/secret','/home/./jjyeung/agent_x','/scratch/./jjyeung/x']:\n files,c=fixture(change=lambda c:c['job'].update(root_parent=path))\n with environment(files):\n  print('path',path,'schema',launch.validate_config(c),'name_hits',anon.scan_text('path',path,rules,'name'))\n  prep(files)\n  print('prepare ACCEPTED normpath',os.path.normpath(path))",
      "output": [
        "path /./data2/secret schema [] name_hits []",
        "prepare ACCEPTED normpath /data2/secret",
        "path /tmp/../data2/secret schema [] name_hits []",
        "prepare ACCEPTED normpath /data2/secret",
        "path /home/./jjyeung/agent_x schema [] name_hits []",
        "prepare ACCEPTED normpath /home/jjyeung/agent_x",
        "path /scratch/./jjyeung/x schema [] name_hits []",
        "prepare ACCEPTED normpath /scratch/jjyeung/x"
      ],
      "expect": "Check normalized path forms as well as their original spelling."
    }
  ],
  "reproduction_context": {
    "instructions": "For each new finding, run python_prelude followed by repro_python in a fresh /usr/bin/python3 -B -c process. The permitted earlier verdict supplies the in-memory fixtures. No filesystem writes or transport calls are needed.",
    "environment": {
      "TMPDIR": "/scratch/jjyeung/orch_n30/e_orchkit-core/tmp",
      "PYTHONPATH": "/scratch/jjyeung/orch_n30/e_orchkit-core/repo/tools"
    },
    "python_prelude": "import json\np='/scratch/jjyeung/orch_n30/e_orchkit-core/work/review/VERDICT_9.json.md'\nwith open(p) as f:v=json.JSONDecoder().raw_decode(f.read())[0]\nexec(v['reproduction_context']['python_prelude'])"
  }
}

All 30 requested reproductions pass their original cases.
Five additional bypasses, OC-32 through OC-36, keep the verdict at NO_GO.
No files changed or jobs were submitted.
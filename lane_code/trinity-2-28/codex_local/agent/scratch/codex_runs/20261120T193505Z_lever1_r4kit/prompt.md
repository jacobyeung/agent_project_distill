# Build: WORD call-placement probe at vehicle N's init (step-400 export) on ReVSI's absolute-distance template (rank 4)

You are a Codex builder on trinity-2-28. Work only inside `/scratch/jjyeung/orch_n30/lever1_c/r4kit/`. Everything else is read-only. No ssh, git, network, GPU, kill, Slurm, deletion outside your folder, or reads/writes of /home or /data*; reads of this node's local /scratch are approved at any volume (do not stop to ask). You BUILD and CPU-TEST; the lane places and submits. Python `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B`, nice 10.

## Question
Does the student at N's init step open a ground call when the absolute-distance question carries ReVSI's wording?

## Frozen design (legality review conditions; hash everything below into `FROZEN.json` BEFORE any generation and state its sha256)
- Template (public text, `in/WORD_TEMPLATES.json`): "Measuring from the closest point of each object, what is the direct distance between the {A} and the {B} (in meters)?" The R0-dev items' own wording differs by one word ("the distance" -> "the direct distance").
- Items: the 290 metre "twin" items of the R0-dev D580 set (their question reads "Measuring from the closest point of each object, what is the distance between the A and the B (in meters)?"); arm ORIG = their wording unchanged, arm REVSI = only "the distance between" replaced by "the direct distance between". Same frames, same everything else. 580 prompts.
- Generation: greedy, at most 64 new tokens, the tower and every tool unserved: stop at the first tool-call opening or at 64 tokens; no tool response is ever served (do not load the grounding or geometry towers if the package allows skipping them; if the package cannot run without loading them, load but never serve).
- Call detector: the exact opening string of the reader's ground call as the step-400 reader parses it (find it in the package's reader source, e.g. the call-tag parser); a prompt "opens a ground call" if that string appears in the generated text within the 64 tokens. Also record any other call type opened.
- Gate: call rate >= 95% on arm REVSI -> no change; under 95% -> report (arm D stays closed; the lane posts it to the orchestrator).
- No item answer, label or truth may be in the job payload (strip them); no score is computed.

## Base package
- `in/D400/` = the step-400 D read that ran these 580 items (Orchard job 173241, package and src/; its RESULT is `in/D400_RESULT.md`), and `in/dk/` its kit. Reuse its placement/CPU-check/submit/fetch pattern, frames and inputs already on Orchard (no re-placement of weights or frames). The checkpoint must be the step-400 export that is N's init, artifact 5083243c...: verify the package's artifact pin starts with 5083243c and report it; if it does not, stop and report.
- Resource: Orchard general partition, gpu:1, 16 CPU, --mem=200G, --exclude=orchard-community-4, worker <= 25 min, allocation <= 30 min; return capped at 50 MB (generated text, call flags, timings). Orchard names: job `a15_cot_ap` + opaque hex, no project/benchmark/dataset/model/method word in any Orchard-visible name, path, argument, env var or log (scan payload member names and scripts against a deny-list: split, vsi, revsi, scannet, arkit, sam, g3t, depth, distill, qwen, ground, dev, bench, mask, tower, reader, student, teacher, k1, t1, word, template).
- Payload size must pass the package's own staging allowance (test the real staging function on the built delivery).

## Deliver
`out/delivery.tgz`, `PLACE.md` (exact place / CPU check / submit / fetch commands in the base kit's style, bytes, sha256), `score.py` (call rates per arm with paired room-bootstrap intervals, 10,000 draws, seed 20261120, and the gate verdict), tests (payload label-free, deny-list, staging, detector on synthetic outputs, 64-token cap), `FROZEN.json` + sha. Forecast GPU minutes from the D400 job's timings. Final message: frozen hashes, forecast, files.

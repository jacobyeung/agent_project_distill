"""Write L/awstrain_20261027/QUEUE_RUNG1.json from this lane's evidence (python3.12, trinity-0-13).

Inputs: out/ADMISSIONS.json (arm -> the ADMISSION.json each code-aws prep job wrote, copied from a poll),
out/BUILD_REPORT.json, out/FROZEN_INPUTS.json, review/REVIEW.json (the independent review), work/COMMIT.txt.
usage: write_queue.py
"""
import hashlib
import json
import math
import os
from pathlib import Path
import time

L = Path("/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/lanes")
HOME = L / "rung1_build_20261027"
QUEUE = L / "awstrain_20261027/QUEUE_RUNG1.json"
ROOT = "/project/community/jjyeung/" + "dis" "till" + "/runs/aws128p_20261025/frozen/"
PARENT = {"parent_run": "q9_l250cp_u2_camrows_ev3_w4_e1_trinity_r1835",
          "weights_sha256": "02bccd997be4eb55cc56ad013fa8f10e56f3f02ca9fbcbe10b64d0123e5450d6",
          "neutral_published_sha256": "70c634a83c0835e679f736de0129d8124d94016b788fea62f5ada5303b0afd04"}
ROLES = {"RG1_A1_S17": ("A1: GT-template traces, vision LoRA on", "G"),
         "RG1_A2_S17": ("A2: A1 rows and targets, vision frozen (targets exact_text_attention_mlp_mergers_vision_frozen)", "G"),
         "RG1_A3_S17": ("A3: GT perception-target traces", "P"),
         "RG1_C_S17": ("answer-only yardstick: fixed 1-in-10 subset of the rows", "X"),
         "RG1_S_S17": ("S: the student's own traces that reached the GT answer (S2V c3r1 on code-aws, up to 2 distinct "
                       "verified samples per question, shortest first); separable shard", "S"),
         "RG1_A1S_S17": ("A1+S mix: every export-G row plus the S rows (same question may train on both trace kinds)", "G+S")}
TRAINER = "299b0c526e3663ff2a42a5c3a9113e9e0b8e4164"  # e343b549 vision-freeze + batch options + exact multi-node microbatch
RECIPE = {"world_size": 32, "nodes": 4, "gpus_per_node": 8, "effective_batch_size": 256, "per_gpu_rows": 8,
          "learning_rate": 0.000283, "max_microbatch_size": 8, "schedule": "cosine, warmup 3%", "epochs": 1, "seed": 17,
          "parallel": "fsdp", "gradient_accumulation": 1}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    admissions = json.loads((HOME / "out/ADMISSIONS.json").read_text()) if (HOME / "out/ADMISSIONS.json").exists() else {}
    frozen = json.loads((HOME / "out/FROZEN_INPUTS.json").read_text())
    report = json.loads((HOME / "out/BUILD_REPORT.json").read_text())
    review_path = HOME / "review/REVIEW.json"
    review = json.loads(review_path.read_text()) if review_path.exists() else None
    arms = []
    for arm, (role, export) in ROLES.items():
        admission = admissions.get(arm)
        pins = frozen.get(arm, {})
        rows = admission["rows"] if admission else (pins["rows_including_heldout_support"] - 1 if pins else None)
        entry = dict(RECIPE, arm=arm, role=role, export=export, frozen_dir=ROOT + arm, training_rows=rows,
                     steps=math.ceil(rows / RECIPE["effective_batch_size"]) if rows else None,
                     checkpoint_every_steps=500, checkpoint_final=True, warm_start=PARENT, trainer_commit=TRAINER,
                     config_sha256=pins.get("config.json", {}).get("sha256"),
                     candidate_index_sha256=pins.get("candidate_index.jsonl", {}).get("sha256"))
        if export in ("S", "G+S"):
            entry["frozen_inputs_built_on"] = "code-aws (selfshard.py; SELF_SHARD_REPORT.json in the S frozen dir)"
        if admission:
            cleared = review and review.get("training_clearance") is True
            entry.update(status="READY" if cleared else "PREPARED_AWAITING_CLEARANCE",
                         bindings=admission["bindings"], protocol_sha256=admission["protocol_sha256"],
                         pre_evaluation_drops=admission["pre_evaluation_drops"], counts=admission["counts"])
        else:
            entry.update(status="PREPARING")
        arms.append(entry)
    queue = {
        "schema": "rung1-queue-v1", "updated_pt": time.strftime("%Y-%m-%dT%H:%M"), "from_lane": "rung1_build_20261027",
        "builder_commit": (HOME / "work/COMMIT.txt").read_text().strip(),
        "rulings": "user 03:00 PT 10-27: every training row carries a trace; A1 GT-template traces; A2 = A1 with vision "
                   "frozen; A3 perception-target traces; a small answer-only control as yardstick only",
        "export": {"source": "gtqgen dispatch export, 293,756 questions (GT answers, bank review rev_qgen PASS)",
                   "kept": report["kept"], "excluded": report["excluded"]},
        "review": ({"path": str(review_path), "sha256": sha(review_path), "verdict": review.get("verdict"),
                    "training_clearance": review.get("training_clearance"), "conditions": review.get("conditions")}
                   if review else {"status": "pending"}),
        "launch": {"night_window_pt": "18:30-06:00 (training up to 62 GPUs); day share 16 GPUs (awstrain SCHEDULE.json)",
                   "gpus_per_arm": 8, "time_limit_per_job": "11:00:00 starting 18:30 PT (ends by 05:30 PT)",
                   "resume": "next window from the newest step_* checkpoint (every 500 steps; final checkpoint kept)",
                   "expected_wall": "about 5.6 s/step on 8 H100: A1/A2 ~14.3 h, A3 ~15 h (longer targets), control ~1.5 h",
                   "wrapper_note": "train_inner.sh pins checkpoint 25 / world 4 / scope aws128-t1-orchard-rung1; these arms "
                                   "need a wrapper variant with checkpoint 500, world 8 and this queue's review record"},
        "arms": arms,
        "extra_shards": {"vsi590k_gt": "vsi590k_gt_20261027/out/QUEUE_RUNG1_EXTRA.json; ARKit rows need frames fetched on "
                                       "code-aws; not prepared by this lane yet",
                         "stage2a_released": "routed to vsi590k_cascade_20261027/INPUT_STAGE2A.jsonl for traces"},
    }
    QUEUE.with_name(QUEUE.name + ".next").write_text(json.dumps(queue, indent=1) + "\n")
    os.replace(QUEUE.with_name(QUEUE.name + ".next"), QUEUE)
    print(json.dumps([{k: a.get(k) for k in ("arm", "status", "training_rows", "steps")} for a in arms]))


if __name__ == "__main__":
    main()

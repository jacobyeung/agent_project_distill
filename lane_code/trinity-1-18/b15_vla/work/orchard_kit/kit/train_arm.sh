#!/bin/bash
#SBATCH --account=mt01
#SBATCH --partition=advanced
#SBATCH --qos=adv_4gpu_qos
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gres=gpu:4
#SBATCH --cpus-per-task=64
#SBATCH --mem=480G
#SBATCH --time=1-00:00:00
#SBATCH --no-requeue
#SBATCH --output=/project/community/jjyeung/vla_libero/logs/slurm_%j.out
# One Test L arm on 4 H100 (design record 4.1, vla_schema_v1): stage, train on LIBERO-Spatial (ZeRO-2, global batch 64,
# arm_testL.yaml) under the stall guard, then evaluate in the same allocation (eval_plan.sh) unless EVAL_IN_JOB=0.
# usage: sbatch -J jjy_vll_<tag> train_arm.sh ARM [SUBSET] [STEPS] [SEED]
#   ARM B1 | U1 (student arms) | B0 (base reference row: refuses to start unless VLL_RULING names the user's ruling,
#   because fresh base or control training needs one). SUBSET d5_s0 (default) | d1_s0 | d50_s0. SEED 17.
#   STEPS 10000 (decisive run, exports 1k/2k/5k/10k) or 1000 (shake-down: export 1k, 100 paired episodes, no claim).
#   Extra trainer overrides: VLL_EXTRA (space separated key=value). The job never retries itself (--no-requeue); a
#   relaunch after a cluster kill waits for the user's answer.
# Disk (node-local /tmp is job-private: Slurm's job_container/tmpfs removes it when the job ends):
#   - milestone saves are weights-only exports (EXPORT_GB, about 20 GiB each); the last one is hard-linked as final_model.
#   - ONE rolling full state (STATE_GB, 121 GiB measured for B1) every trainer.state_every steps, replaced atomically.
#   - preflight: refuses to train unless /tmp has 2 x STATE_GB + n_exports x EXPORT_GB + 10 GiB free after staging.
#   - copy rule: exports and the state stay node-local and are evaluated in this allocation; at the end the final weights
#     go to $V/runs/<id>/final_model if /project keeps > 80 GiB free (KEEP_FINAL=1). If training fails, the state is copied
#     to $V/runs/<id>/resume_state only with COPY_STATE=1 and /project holding >= 2 x its size; otherwise it is lost with
#     /tmp. RESUME_FROM=<state dir> resumes from such a copy (same world size).
set -uo pipefail; . /project/community/jjyeung/vla_libero/kit/vl_env.sh
ARM=$1 SUB=${2:-d5_s0} STEPS=${3:-10000} SEED=${4:-17}
case $ARM in
  B1) ;;
  U1) [ -n "${WHERE_CACHE:-}" ] || { echo "REFUSED: U1 needs the where-provider cache (WHERE_CACHE) and its loader, not built yet"; exit 4; } ;;
  B0) [ -n "${VLL_RULING:-}" ] || { echo "REFUSED: B0 is control-only (vla.control_only: true) and stays disabled until the user's explicit yes; set VLL_RULING=<that ruling>"; exit 4; } ;;
  *) echo "REFUSED: unknown arm $ARM"; exit 4 ;;
esac
id=${ARM}_sp${SUB}_s${SEED}_k$((STEPS / 1000)); P=$V/runs/$id; mkdir -p $P
export B=/tmp/vll_${SLURM_JOB_ID:-local}; R=$B/runs; mkdir -p $R $B/xdg; cp -r $K $B/kit && export K=$B/kit;  # jobs run a private snapshot of the kit
export XDG_CACHE_HOME=$B/xdg TRITON_CACHE_DIR=$B/triton
exec > >(tee -a $P/job_${SLURM_JOB_ID:-local}.log) 2>&1
ph() { echo "$(date -u +%FT%TZ) $*" | tee -a $P/phase.log; }
ph "start host=$(hostname) job=${SLURM_JOB_ID:-} arm=$ARM sub=$SUB steps=$STEPS seed=$SEED ruling=${VLL_RULING:-} gpus=${CUDA_VISIBLE_DEVICES:-} kit=$(head -c 16 $K/KIT_SHA256 2>/dev/null)"
( nvidia-smi --query-gpu=index,name,memory.total --format=csv; df -h /tmp | tail -1 ) | tee -a $P/phase.log
bash $K/stage.sh $ARM || { ph "FAIL stage"; exit 1; }
ph "staged $(cat $B/models/Qwen3.5-$ARM/B1_CHECK.json 2>/dev/null | head -c 300)"
NG=$(nvidia-smi -L | wc -l); BS=$((64 / NG)); STATE_GB=${STATE_GB:-125} EXPORT_GB=${EXPORT_GB:-20}
sed "s#KITDIR#$K#" $K/acc_z2.yaml > $B/acc.yaml
WU=$(( STEPS * 3 / 100 ))
SAVES=$(python3 -c "import sys; s=int(sys.argv[1]); print(','.join(str(x) for x in (1000, 2000, 5000, 10000) if x <= s) or s)" $STEPS)
NEXP=$(echo $SAVES | tr ',' '\n' | wc -l)
pf=$(bash $K/preflight.sh $R $(( 2 * STATE_GB + NEXP * EXPORT_GB + 10 )) "train $id: 2x${STATE_GB} state + ${NEXP}x${EXPORT_GB} exports + 10"); pfrc=$?; ph "$pf"
[ $pfrc = 0 ] || { ph "REFUSED: node-local disk too small for this arm's saves"; exit 4; }
ov=(--run_root_dir=$R --run_id=$id --seed=$SEED --framework.qwenvl.base_vlm=$B/models/Qwen3.5-$ARM
    --datasets.vla_data.data_root_dir=$B/data/lerobot --datasets.vla_data.data_mix=vll_libero_spatial_$SUB --datasets.vla_data.per_device_batch_size=$BS
    --trainer.max_train_steps=$STEPS --trainer.num_warmup_steps=$WU "--trainer.save_steps=[$SAVES]"
    --trainer.state_gb_est=$STATE_GB --trainer.export_gb_est=$EXPORT_GB)
[ $ARM = U1 ] && ov+=(--framework.vla_heads.cond=spatial_readouts)
[ -n "${RESUME_FROM:-}" ] && ov+=(--trainer.resume_state=$RESUME_FROM)
for kv in ${VLL_EXTRA:-}; do ov+=(--$kv); done
CO=false; [ $ARM = B0 ] && CO=true  # schema v2: every control-only arm carries vla.control_only: true
mkdir -p $R/$id; cp $K/arm_testL.yaml $R/$id/launch.yaml; { printf '%s\n' "${ov[@]}"; echo "# vla.control_only: $CO ruling: ${VLL_RULING:-none}"; } > $R/$id/launch_overrides.txt; cp $R/$id/launch*.* $P/
if [ ! -f $R/$id/TRAIN_COMPLETE ]; then
  ( cd $SV && train_env && exec accelerate launch --config_file $B/acc.yaml --num_processes $NG --mixed_precision bf16 --main_process_port 29517 \
      $K/vl_train.py --config_yaml $K/arm_testL.yaml "${ov[@]}" ) > $R/$id/train.log 2>&1 &
  tp=$!
  bash $K/stall_watch.sh $tp $R/$id/trace.jsonl $P 20 45 &
  ( while kill -0 $tp 2>/dev/null; do for f in trace.jsonl metrics.jsonl summary.jsonl config.yaml dataset_statistics.json proprio_norm.json action_norm.json prompt_template.json STOP_REASON.json; do [ -f $R/$id/$f ] && cp $R/$id/$f $P/; done; tail -50 $R/$id/train.log > $P/train_tail.log; sleep 300; done ) &
  wait $tp; rc=$?
  for f in trace.jsonl metrics.jsonl summary.jsonl config.yaml dataset_statistics.json proprio_norm.json action_norm.json prompt_template.json STOP_REASON.json train.log; do [ -f $R/$id/$f ] && cp $R/$id/$f $P/; done
  ph "train rc=$rc $(cat $P/STOP_REASON.json 2>/dev/null)"; ph "disk $(df -h $R | tail -1) saves $(grep -c '"kind"' $R/$id/summary.jsonl 2>/dev/null)"
  if [ ! -f $R/$id/TRAIN_COMPLETE ]; then
    S=$(readlink -f $R/$id/state/current 2>/dev/null)
    if [ -n "$S" ] && grep -q '"step": [1-9]' $S/vl_meta.json 2>/dev/null; then
      sz=$(du -sBG $S | cut -f1 | tr -dc 0-9); pfree=$(df -BG --output=avail $V | tail -1 | tr -dc 0-9)
      if [ "${COPY_STATE:-0}" = 1 ] && [ "${pfree:-0}" -ge $(( 2 * sz )) ]; then
        cp -r $S $P/resume_state.partial && mv $P/resume_state.partial $P/resume_state && ph "state $(cat $S/vl_meta.json) copied to $P/resume_state (${sz}G; /project had ${pfree}G)"
      else
        ph "state $(cat $S/vl_meta.json) NOT copied (${sz}G; /project ${pfree}G free; COPY_STATE=${COPY_STATE:-0}); it is lost with /tmp at job end"
      fi
    fi
    ph "FAIL train incomplete"; exit 1
  fi
fi
if [ "${EVAL_IN_JOB:-1}" = 1 ]; then
  bash $K/eval_plan.sh $R/$id $P/eval $STEPS; ph "eval_plan rc=$?"
fi
free=$(df -BG --output=avail $V | tail -1 | tr -dc 0-9)
if [ "${KEEP_FINAL:-1}" = 1 ] && [ "${free:-0}" -gt $(( 80 + EXPORT_GB )) ]; then
  mkdir -p $P/final_model; cp $R/$id/final_model/pytorch_model.pt $P/final_model/; ph "final weights kept in $P/final_model ($free GB were free)"
else
  ph "final weights NOT kept on /project ($free GB free, need > $(( 80 + EXPORT_GB )); KEEP_FINAL=${KEEP_FINAL:-1}); they are lost when Slurm removes /tmp at job end"
fi
ph "ARM_DONE $id"

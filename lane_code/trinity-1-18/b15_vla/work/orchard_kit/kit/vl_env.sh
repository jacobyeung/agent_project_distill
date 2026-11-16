# Sourced by every kit script. train_env / sim_env <libero|plus> / tool_env set PATH and PYTHONPATH.
V=${V:-/project/community/jjyeung/vla_libero}; K=${K:-$V/kit}; SV=$V/src/starVLA-pilot; DATA=${DATA:-$V/data/lerobot}; FULL=$DATA/libero_spatial_no_noops_1.0.0_lerobot
export V K SV DATA FULL STARVLA_DIR=$SV
export XDG_CACHE_HOME=${XDG_CACHE_HOME:-$V/cache/xdg} PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 MPLCONFIGDIR=$V/cache/mpl
export HF_HOME=$V/cache/hf HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 WANDB_MODE=disabled TOKENIZERS_PARALLELISM=false
export TRITON_CACHE_DIR=${TRITON_CACHE_DIR:-$V/cache/triton} TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1
unset HF_TOKEN HUGGING_FACE_HUB_TOKEN GOOGLE_API_KEY GEMINI_API_KEY OPENAI_API_KEY
train_env() { export PATH=$V/envs/e_sv/bin:$V/bin:/usr/local/bin:/usr/bin:/bin PYTHONPATH=$SV:$K:$K/ext_v2/vla_heads:$K/ext_where; }
tool_env() { export PATH=$V/envs/e_tool/bin:$V/bin:/usr/local/bin:/usr/bin:/bin PYTHONPATH=$K; }
sim_env() {
  local t=${1:-libero}
  export LIBERO_CONFIG_PATH=$V/cfg/$t
  if [ "$t" = plus ]; then export LIBERO_HOME=$V/src/LIBERO-plus-main; else export LIBERO_HOME=$V/src/LIBERO-master; fi
  export PYTHONPATH=$K/shims:$LIBERO_HOME:$SV:$K PATH=$V/envs/e_lb/bin:$V/bin:/usr/local/bin:/usr/bin:/bin
  [ -d $V/osmesa/lib ] && export LD_LIBRARY_PATH=$V/osmesa/lib:${LD_LIBRARY_PATH:-}
  export MUJOCO_GL=${MUJOCO_GL:-$(cat $V/st/gl 2>/dev/null || echo egl)}; export PYOPENGL_PLATFORM=$MUJOCO_GL
}

# Sourced by every control wrapper before launching Python.
export CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false
control_root="${READ228_CONTROL_ROOT:-/scratch/jjyeung/orch_n30/reads228/control}"
control_root="$(realpath -m -- "$control_root")"
case "$control_root" in /scratch/jjyeung/*) ;; *) echo 'REFUSED: control files require local scratch' >&2; exit 2;; esac
export HOME="$control_root/home" TMPDIR="$control_root/tmp"
export XDG_CACHE_HOME="$control_root/cache" XDG_CONFIG_HOME="$control_root/config"
export XDG_DATA_HOME="$control_root/data" XDG_STATE_HOME="$control_root/state"
export CUDA_CACHE_PATH="$XDG_CACHE_HOME/nv" MPLCONFIGDIR="$XDG_CACHE_HOME/mpl"
export HF_HOME="$XDG_CACHE_HOME/hf" TRITON_CACHE_DIR="$XDG_CACHE_HOME/triton"
export TORCH_HOME="$XDG_CACHE_HOME/torch" TORCHINDUCTOR_CACHE_DIR="$XDG_CACHE_HOME/inductor"
export USER=jjyeung LOGNAME=jjyeung PATH=/usr/local/bin:/usr/bin:/bin
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
unset LD_LIBRARY_PATH PYTHONPATH PYTHONHOME H10_SETTINGS
nice -n 10 mkdir -p "$HOME" "$TMPDIR" "$XDG_CACHE_HOME" "$XDG_CONFIG_HOME" "$XDG_DATA_HOME" "$XDG_STATE_HOME" \
  "$CUDA_CACHE_PATH" "$MPLCONFIGDIR" "$HF_HOME" "$TRITON_CACHE_DIR" "$TORCH_HOME" "$TORCHINDUCTOR_CACHE_DIR"

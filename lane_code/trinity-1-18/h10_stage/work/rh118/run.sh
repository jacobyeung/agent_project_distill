W=/scratch/jjyeung/orch_n30/h10_stage/work; R=/scratch/jjyeung/b01ec87a6f29b
export CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1 TOKENIZERS_PARALLELISM=false
export TMPDIR=$W/rh118/tmp HOME=$W/rh118/home XDG_CACHE_HOME=$W/rh118/cache; mkdir -p $TMPDIR $HOME $XDG_CACHE_HOME
bash $W/rh118/build.sh > $W/rh118/build.log 2>&1 || { echo build failed; exit 1; }
nice -n 10 $R/d/v/py_rh -B -I $W/rh118/prep.py > $W/rh118/prep.log 2>&1; echo "prep rc=$?" >> $W/rh118/prep.log
nice -n 10 $R/d/v/py_rh -B -I $W/rh118/worker.py > $W/rh118/worker.log 2>&1; echo "worker rc=$?" >> $W/rh118/worker.log

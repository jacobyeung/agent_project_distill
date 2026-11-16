sha256sum /scratch/jjyeung/envs/vllm/requirements.freeze.txt /scratch/jjyeung/envs/vllm/conda-explicit.txt /scratch/jjyeung/envs/vllm/bin/python3.12
timeout 120 /scratch/jjyeung/envs/vllm/bin/python -c "import vllm,transformers,torch;print(vllm.__version__,transformers.__version__,torch.__version__)" 2>&1 | tail -1
ls -d /scratch/jjyeung/k1_frames /scratch/jjyeung/orch_n30/b11_presence /scratch/jjyeung/orch_n30/trin_read/root/sj/apb59bef09f3/p/reader 2>&1

R=/project/community/jjyeung/vla_libero
cd $R/kit && sha256sum -c SHA256SUMS 2>&1 | grep -v ': OK$' | head -20; echo "SUMS_LINES $(wc -l < SHA256SUMS)"; cat KIT_SHA256; sha256sum SHA256SUMS
cd $R && du -sh kit out work/tiny_Qwen3.5 work/hook_runs work/rotate_runs work/cache_mask_check src envs/e_sv envs/e_lb envs/e_tool data/lerobot data/hdf5 osmesa py 2>&1
ls -la out/cpu_hook out/cpu_rotate out/cl_check out/conformance out/subsets out/prep 2>&1 | head -80
ls -la data/lerobot data/hdf5 work/tiny_Qwen3.5 2>&1 | head -40
cat kit/RULINGS.md; cat out/conformance_run.log

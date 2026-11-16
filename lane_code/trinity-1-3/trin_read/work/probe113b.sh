B=/scratch/jjyeung/orch_n30/native_r2/work/base/models--Qwen--Qwen3.5-9B/snapshots
ls -la $B; for s in $B/*; do ls -laL $s; for f in config.json chat_template.jinja preprocessor_config.json video_preprocessor_config.json tokenizer_config.json model.safetensors.index.json; do sha256sum $s/$f 2>&1; done; done

hostname -s | cut -c1-12
ls -la /data2/k6tk/54/5434c2265b166c943c3a67b94fcecce2ac913e7349f99409826c7cf959dc177f.png 2>&1 | cut -c1-200
ls -d /data2/k6tk 2>&1 | head -2
ls /lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap 2>/dev/null | head -30
python3 -c "import PIL; print('PIL', PIL.__version__)" 2>&1 | tail -1

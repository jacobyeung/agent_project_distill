F=/scratch/jjyeung/orch_n30/fb_pack; grep -n -i "fov" $F/donor3/out/REPORT.md $F/donor3/out/READER_REQUEST.md | cut -c1-400 | head -20; sed -n 1,20p $F/donor3/out/READER_REQUEST.md | cut -c1-300
tmux ls | grep fbp | cut -d: -f1; ls $F/patchA2rev

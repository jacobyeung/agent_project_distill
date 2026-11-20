export TZ=UTC
hostname; date -u +%FT%TZ
sinfo -s 2>&1 | head -20
sinfo -p preempt -o '%P %a %l %D %c %m %G %t' 2>&1 | head
squeue -u jjyeung -o '%i %j %P %T %M %R' 2>&1 | head
P=/project/community/jjyeung/b9ef552934627; ls -la $P | head -40
df -h /project/community/jjyeung 2>&1 | tail -2
which python3; python3 -c "import PIL, numpy; print('PIL', PIL.__version__, 'np', numpy.__version__)"
ls /tmp/nvk1 2>&1 | head

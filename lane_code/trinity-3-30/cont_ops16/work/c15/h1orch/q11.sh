O=/project/community/jjyeung/okh7; B=$O/i_1be16f28
pgrep -af 'i_1be16f28/g.sh' | head -2
ls -ld /scratch /scratch/fsw /scratch/fsw/portfolios /lustre /lustre/fsw /lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung 2>&1
mount | grep -E ' /scratch| /lustre| / ' | head -5 | cut -c1-200
ls $B | tr '\n' ' '; echo; ls $B/u $B/c 2>&1 | head; ls -la $B/gate.json 2>&1
wc -l $O/t_c94bbc4e.g.log; grep -v ': OK$' $O/t_c94bbc4e.g.log | cut -c1-300
/project/community/jjyeung/cp4tk_rt/kit/bwrap --version 2>&1; uname -r

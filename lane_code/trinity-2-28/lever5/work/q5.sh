cd /project/community/jjyeung/a3b73b53d92a7
tar xOzf 0.tgz 8.py | grep -n -o -E ".{0,200}(sbatch|exclude|Popen|subprocess\.run|env=).{0,200}" | head -20
man sbatch 2>/dev/null | col -b | grep -n -E '^ +SBATCH_(HOLD|NODELIST|EXCLUDE|BEGIN)' | head
scontrol show node orchard-community-1 | grep -E 'Gres|AllocTRES|CfgTRES|State'

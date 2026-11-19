export TZ=UTC
scontrol show node -d orchard-community-2 | grep -i "gres" | head -5
grep -iv "^#" /etc/slurm/gres.conf 2>/dev/null | grep -i "community\|type\|name" | head -8
ls /etc/slurm/ 2>/dev/null | head -20 | tr '\n' ' '; echo
grep -il "H100\|A100\|NVIDIA" /project/community/jjyeung/okh7/x_22c714e1/j/*.out 2>/dev/null | head -3
grep -ih "NVIDIA H100\|NVIDIA A100\|H100 80GB\|device name" /project/community/jjyeung/okh7/x_22c714e1/j/*.out 2>/dev/null | head -3

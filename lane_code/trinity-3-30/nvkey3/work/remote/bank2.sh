K=/scratch/jjyeung/orch_n30/nvkey1/work; cd $K || exit 1
DST=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/nvkey/bank_trinity; mkdir -p $DST
[ -f $DST/nvkey_trinity_bank_20261120.tgz ] || cp bank/nvkey_trinity_bank_20261120.tgz $DST/
tar tzvf bank/nvkey_trinity_bank_20261120.tgz | awk '{print $3, $6}' > bank/MANIFEST.txt; sha256sum bank/nvkey_trinity_bank_20261120.tgz > bank/SHA256.txt
[ -f $DST/MANIFEST.txt ] || cp bank/MANIFEST.txt bank/SHA256.txt $DST/
ls -la $DST; sha256sum $DST/nvkey_trinity_bank_20261120.tgz | cut -c1-64; wc -l $DST/MANIFEST.txt

cd /scratch/jjyeung/n30_mirror/corpus_work; cat DONE; ls -la *.list
for f in *.list; do echo "== $f"; grep -E "(FETCH\.json|/result\.tar\.gz|items_a0\.jsonl|/journals/.*/items\.jsonl|decode\.jsonl|budget_[0-9]+\.jsonl)$" $f | grep -v -E "evidence/test_|test_tmp|pytest|/tests?/|chain_|test_runs|fix1c_" | awk '{printf "%.1fM %s\n",$3/1e6,$6}' | head -150; done

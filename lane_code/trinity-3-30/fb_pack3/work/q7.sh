F=/scratch/jjyeung/orch_n30/fb_pack; cat $F/patchA2rev/REVIEW_VERDICT.md | cut -c1-700 | head -40; sha256sum $F/patchA2rev/REVIEW_VERDICT.md | cut -c1-16

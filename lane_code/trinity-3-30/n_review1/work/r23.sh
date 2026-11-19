M=/scratch/jjyeung/orch_n30/n_review; W=/scratch/jjyeung/orch_n30/tree_rebuild10_w
cd $M && tar cf - vqa_sample40.json vqa_scan.json vqa_counts.json twins_check.json ident_out.json ident.py samp_vqa.py scan_vqa.py twins.py | base64 -w0

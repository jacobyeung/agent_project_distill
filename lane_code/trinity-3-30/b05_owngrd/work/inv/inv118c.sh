cd /scratch/jjyeung
echo ==tar; head -c 2000000000 k1/m544_parts/469ddece_mstop.tar.part00-of-04 | tar tvf - 2>/dev/null | head -40
echo ==qwen; ls trinity_qwen qwen_port_1110 qwen_gate_1114 2>/dev/null | head -30
echo ==orchcd; for d in sam3_tower ttower label_ops mdg_build mdg_next own_probe ofs_e1 dose_pool k1_build evalx; do echo "$d $(du -sh orch_cd/$d 2>/dev/null | cut -f1) $(find orch_cd/$d -maxdepth 3 -type d 2>/dev/null | head -8 | tr '\n' ' ')"; done
ls -la orch_cd/ttower/work/sam3_weights 2>/dev/null
ls orch_cd/dose_pool/out 2>/dev/null; ls orch_cd/dose_pool/out/t1_gt 2>/dev/null | head

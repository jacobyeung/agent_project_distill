timeout 120 find /scratch/jjyeung -maxdepth 7 \( -name 'metadata_e10fbb95*' -o \( -path '*469ddece/inputs*' -name 's1_receipt.json' \) \) 2>/dev/null | head
echo ==trin_read3; ls /scratch/jjyeung/orch_n30 | head -50

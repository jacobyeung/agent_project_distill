import re,tarfile,os,sys
W=re.compile(r'split|revsi|vsi|vsti|bench|distill|qgen|scannet|arkit|qwen|student|room|units|facing|loader|audit|away|teacher|vqa|routing|pilot|carrier',re.I)
# visible = file names in archive top-level and records/ and proof/, argv in s.sh/p_*.sh/jb.sh sbatch lines
for root,ds,fs in os.walk('arch'):
    if root.startswith('arch/t'):continue
    for f in fs:
        if W.search(f):print('NAME',os.path.join(root,f))

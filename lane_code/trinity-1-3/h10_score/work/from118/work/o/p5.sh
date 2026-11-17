W=/project/community/jjyeung/okh7/e6fc152498; cd $W
for g in 0 1 2; do echo "== g$g top"; awk '{print $6}' g$g.list | awk -F/ '{print $1"/"$2"/"$3"/"$4}' | sort | uniq -c | sort -rn | head -12
echo "== g$g dist"; grep -o -E '[^/ ]+\.dist-info/$' g$g.list | sort -u | grep -i -E '^(torch|torchvision|transformers|scipy|numpy|timm|iopath|portalocker|ftfy|pycocotools|wcwidth|flash_linear|fla|causal|tokenizers|huggingface_hub|safetensors|pillow|accelerate|peft|regex|einops|triton|packaging|hydra|omegaconf|decord|psutil|tqdm)' 
echo "== g$g term"; grep -i -E 'terminator|vnice' g$g.list | head
echo "== g$g python"; grep -E '/bin/python[0-9.]* ' g$g.list | head -5; grep -c 'pyvenv.cfg' g$g.list
done
grep -E 'pyvenv.cfg' g0.list g1.list g2.list

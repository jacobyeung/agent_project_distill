"""Run at the staged frame root to verify pins and measure the exact tar payload size."""
import argparse,json
from pathlib import Path
from devs1_anchors import verify_frames,save
p=argparse.ArgumentParser();p.add_argument('--frame-root',required=True);p.add_argument('--out',required=True);a=p.parse_args()
plan=json.loads(Path(__file__).with_name('PLAN.json').read_text());total=verify_frames(plan,a.frame_root)
save(a.out,dict(files=len(plan['files']),bytes=total));print(total)

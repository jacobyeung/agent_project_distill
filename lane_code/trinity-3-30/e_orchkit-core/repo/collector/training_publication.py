"""Publish all teacher outcomes without hiding errors or rewriting answers."""
import json,os
from pathlib import Path
from training_assets import enter_episode,current_archive

def final_dir(output,qid): return Path(output)/'finalized'/qid

def publish_finalized_triple(output,qid,raw,receipt):
    enter_episode(qid)
    target=final_dir(output,qid)
    target.mkdir(parents=True,exist_ok=False)
    # The clean projection is lossless for training. No model output is shortened.
    for name,value in [(f'trace_{qid}.json',raw),(f'trace_{qid}_clean.json',raw),('attempt.json',receipt)]:
        with (target/name).open('x') as handle:
            json.dump(value,handle,ensure_ascii=False,default=str)
            handle.write('\n');handle.flush();os.fsync(handle.fileno())
    current_archive().event('published',{'question_id':qid,'path':str(target)})
    return target

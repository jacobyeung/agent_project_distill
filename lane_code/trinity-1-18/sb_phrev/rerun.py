"""Re-execute all part-1 pools from source caches; writes only in this review workspace."""
import hashlib, json, os, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent / 'sb_mask_phrase'

def main():
    if len(sys.argv) == 1:
        cpus = sorted(os.sched_getaffinity(0))
        assert len(cpus) >= 8
        jobs = []
        for shard in range(4):
            log = (ROOT / f'rerun_{shard}.log').open('w')
            jobs.append(subprocess.Popen(['taskset', '-c', ','.join(map(str, cpus[2*shard:2*shard+2])),
                                         sys.executable, '-B', __file__, str(shard)], stdout=log, stderr=subprocess.STDOUT))
        codes = [p.wait() for p in jobs]
        print('worker exit codes', codes, flush=True)
        assert codes == [0]*4
        return
    sys.path.insert(0, str(SOURCE))
    import kit as K
    shard = int(sys.argv[1])
    caps, ctx = K.setup(threads=2)
    common = dict(K.T.PINS)
    common[str(Path(__file__))] = K.sha(__file__)
    common[str(ROOT/'run_review.sh')] = K.sha(ROOT/'run_review.sh')
    folder = ROOT/'rerun_caps'
    folder.mkdir(exist_ok=True)
    for c in sorted(caps, key=lambda x: x['canonical'])[shard::4]:
        K.T.PINS.clear(); K.T.PINS.update(common)
        rec = K.capture(c, ctx)
        rec['input_sha256'] = dict(K.T.PINS)
        rec['command'] = f'bash run_review.sh rerun.py (worker {shard}/4; two CPU affinity slots)'
        K.write_gz(folder/(K.stub(c)+'.json.gz'), rec)
        print(c['canonical'], round(rec['seconds'], 2), rec['peak_rss_mib'], flush=True)

if __name__ == '__main__':
    main()

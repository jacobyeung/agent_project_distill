"""Dry-run step 4a: SAM 3's video predictor from the pinned checkpoint on CPU, unmodified, with its exact failure.

Tries build_sam3_video_predictor (multi-GPU wrapper) and Sam3VideoPredictor, each once; the CPU tracker pass instead
builds the same model (build_sam3_video_model, strict loading) and uses its tracker (mc_tracker.Sam3Carry).
Usage: python mc_probe_predictor.py   (SAM 3 interpreter, CUDA hidden; writes out/v2/dry/PREDICTOR_CPU.json)
"""
import json, resource, time, traceback
import mc_common as C
import mc_tracker as MT


def attempt(label, build):
    t0 = time.monotonic()
    try:
        obj = build()
        out = dict(status='LOADED', type=type(obj).__name__)
        del obj
    except BaseException as exc:
        tb = traceback.extract_tb(exc.__traceback__)
        out = dict(status='FAILED', error=f'{type(exc).__name__}: {exc}', raised_at=f'{tb[-1].filename}:{tb[-1].lineno} {tb[-1].line}',
                   frames=[f'{f.filename.replace(str(C.SAM3_ROOT)+"/", "")}:{f.lineno} {f.name}' for f in tb][-6:])
    out.update(label=label, seconds=time.monotonic()-t0, peak_rss_gib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/2**20)
    return out


def main():
    MT.verify_sources()
    MT.verify_checkpoint()
    MT.import_sam3()
    import torch
    torch.set_num_threads(8)
    from sam3.model_builder import build_sam3_video_predictor
    from sam3.model.sam3_video_predictor import Sam3VideoPredictor
    rec = dict(step='dry-run step 4a: SAM 3 video predictor on CPU', torch=torch.__version__, cuda_available=torch.cuda.is_available(),
               checkpoint=str(C.CHECKPOINT), attempts=[
                   attempt('build_sam3_video_predictor(checkpoint_path=pinned)', lambda: build_sam3_video_predictor(checkpoint_path=str(C.CHECKPOINT))),
                   attempt('Sam3VideoPredictor(checkpoint_path=pinned)', lambda: Sam3VideoPredictor(checkpoint_path=str(C.CHECKPOINT)))])
    rec['status'] = 'LOADED' if any(a['status'] == 'LOADED' for a in rec['attempts']) else 'FAILED_AS_RECORDED'
    rec['consequence'] = ('the predictor classes need CUDA; the CPU dry run and the GPU pass build the same model with '
                          'build_sam3_video_model(strict) and call its tracker (Sam3TrackerPredictor) directly')
    C.write_json(C.OUT/'dry/PREDICTOR_CPU.json', rec)
    print(json.dumps({a['label']: (a['status'], a.get('error'), round(a['seconds'], 1)) for a in rec['attempts']}), flush=True)
    C.status('Dry-run step 4a (PREDICTOR_CPU.json): ' + '; '.join(f"{a['label'].split('(')[0]} {a['status']} {a.get('error', '')[:90]}"
                                                                   for a in rec['attempts']))


if __name__ == '__main__':
    main()

"""Test 2 (CPU, gloo, two ranks): the rehearsal's save part (rh/sx.py) on the tree's own tiny fixture model.
Each rank runs two native optimize steps, then sx.save_export with the job's disk policy, recipe and
r2_identity (from the kit's k/n.json): one checkpoint and one export into <out>/sink, each archived by
launch_r2.persistence (local_only, as the job's config has no r2_persistence). Then the same with a policy
whose reserve no disk can hold, which the guard must refuse before writing a state. Rank 0 reloads the
export with the tree's load_artifact. Results in <out>/t2_result.json.
usage (inside the test sandbox): t2_save.py <out> <kit> ; PYTHONPATH=<tree>:<rh>"""
import base64, json, os, sys, time, traceback
from pathlib import Path
import torch
import torch.distributed as dist

out, kit = Path(sys.argv[1]), Path(sys.argv[2])


def read(p):
    v = json.loads(Path(p).read_text())
    return json.loads(base64.b64decode(v['payload'])) if 'payload' in v else v


job = read(kit / 'k/n.json')
WORLD = int(os.environ.get('A15_T2_WORLD', '2'))


def worker(rank, port):
    torch.set_num_threads(1)
    log = out / 'log'; log.mkdir(exist_ok=True)
    def ev(kind, **kw):
        with open(log / f'ev_rank{rank}.jsonl', 'a') as f:
            f.write(json.dumps(dict(t=round(time.time(), 3), rank=str(rank), kind=kind, **kw), default=str) + '\n')
    dist.init_process_group('gloo', init_method=f'tcp://127.0.0.1:{port}', rank=rank, world_size=WORLD)
    result = dict(rank=rank)
    try:
        from student_pilot import carrier_c1_run as run, full_ft
        from student_pilot.carrier_c1 import parameter_groups
        from student_pilot.carrier_c1_data import mixed_indices
        from student_pilot.p3_provenance import file_pin
        from tests.test_carrier_c1 import fixture
        from tests.test_carrier_c1_run import FixtureRows
        import sx
        model, _, _ = fixture(4)
        wrapped = run.wrap_model(model, torch.device('cpu'), mixed_precision=False)
        optimizer = torch.optim.AdamW(parameter_groups(wrapped), weight_decay=.01)
        rows = FixtureRows(); plans = list(mixed_indices(dict(pose=9, vqa=9, pointing=9), 2))
        for step in (1, 2):
            run.optimize_step(wrapped, optimizer, rows, plans[step - 1], rank, torch.device('cpu'), step, True)
        policy = job['checkpoint_disk_guard']
        cfg = dict(base_identity='fixture', trace_program_version='3.13', checkpoint_disk_guard=policy)
        pcfg = dict(cfg, recipe=job['recipe'], r2_identity=job['r2_identity'],
                    r1_training={'a15_test': 'persistence reads only the presence of this key'})
        bound = dict(fixture='a15_t2', world_size=WORLD)
        saved = sx.save_export(run, model, wrapped, optimizer, cfg, bound, rank, 2, out / 'sink', ev=ev, persist_cfg=pcfg)
        result.update(state=str(saved['state']), export=str(saved['export']), guards=saved['guards'])
        if rank == 0:
            fresh, batch, target = fixture(4)
            artifact = run.load_artifact(fresh, file_pin(out / 'sink/m2/artifact.json'))
            result['reload'] = dict(step=artifact['step'], finite=fresh.eval().probe(batch, target)['finite'])
        # the guard must refuse a plan no disk can hold, before any state is written
        big = dict(policy, reserve_bytes=10 ** 16)
        try:
            sx.save_export(run, model, wrapped, optimizer, dict(cfg, checkpoint_disk_guard=big), bound, rank, 2,
                           out / 'sink_refuse', ev=ev, persist_cfg=dict(pcfg, checkpoint_disk_guard=big))
            result['refusal'] = 'NOT REFUSED'
        except ValueError as e:
            result['refusal'] = str(e)[:300]
        result['status'] = 'PASS'
    except BaseException as e:
        result.update(status='FAIL', error=f'{type(e).__name__}: {e}', traceback=traceback.format_exc()[-6000:])
        raise
    finally:
        (out / f't2_rank{rank}.json').write_text(json.dumps(result, indent=1, default=str) + '\n')
        dist.destroy_process_group()


def audit(event, arguments):
    # the tree's test harness hook refuses every removal; library temporary files under <out>/tmp may go,
    # nothing else (the sink is never cleared)
    if event in ('os.remove', 'os.rmdir', 'os.unlink', 'shutil.rmtree'):
        path = Path(os.fsdecode(arguments[0])).absolute()
        if not path.is_relative_to(out / 'tmp'):
            raise PermissionError('The test retains its artifacts: ' + str(path))


if __name__ == '__main__':
    from tests.retained_workers import run_workers
    run_workers(worker, (), world=WORLD, timeout=900, start_method='fork')
    print('workers done')

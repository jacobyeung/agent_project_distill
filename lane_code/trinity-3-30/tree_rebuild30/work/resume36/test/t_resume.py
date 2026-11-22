"""Resume test on the tree's fixture model, gloo, CPU (Trinity only). Every phase runs inside bwrap with the
phase's run folder bound at the fixed namespace NS, as the kit binds Q_ROOT at Q_NS.
  A    the dying allocation: binding from v.json exactly as train() forms it; bind_output; run_steps from step 0
       with a save every step and stop_after_step=2; the newest state goes through launch_r2.persistence
       (local_only archive copy, as N's config has r2_identity and no r2_persistence). Then a control run from
       the same init straight to step 3 in a separate output, for the bitwise comparison.
  B    the resumed allocation (fresh processes, other run folder, the state staged by b/rs.py): the tree's own
       refusals for a foreign preparation pin, latest_resume, restore, bind_output(resume=True), the refusal of
       a fresh start over a complete state, then run_steps from the restored step for one step with
       stop_after_step=3 (checkpoint, export at stop), and persistence on the new state.
usage: t_resume.py A|B <out json dir>  (PYTHONPATH=<tree>; env RS_WORLD, RS_NS, SLURM_JOB_ID)"""
import hashlib, json, os, random, sys, time, traceback
from pathlib import Path
import numpy as np
import torch
import torch.distributed as dist

phase, out = sys.argv[1], Path(sys.argv[2])
WORLD, NS = int(os.environ.get('RS_WORLD', '4')), Path(os.environ['RS_NS'])


def digests(wrapped):
    from student_pilot import full_ft
    h = hashlib.sha256()
    for name, p in full_ft.named_trainable(wrapped):
        h.update(name.encode()); h.update(p.detach().cpu().contiguous().numpy().tobytes())
    return h.hexdigest()


def seed():
    torch.manual_seed(17); random.seed(17); np.random.seed(17)


def worker(rank, port):
    torch.set_num_threads(1)
    dist.init_process_group('gloo', init_method=f'tcp://127.0.0.1:{port}', rank=rank, world_size=WORLD)
    result = dict(rank=rank, phase=phase)
    try:
        from student_pilot import carrier_c1_run as run
        from student_pilot.carrier_c1 import parameter_groups
        from student_pilot.carrier_c1_sweep import recipe_for
        from student_pilot.p3_provenance import load, write, file_pin
        from launch_r2 import persistence
        from tests.test_carrier_c1 import fixture
        from tests.test_carrier_c1_run import FixtureRows
        job = load(NS / 'v.json')
        # train() line for line: bound=dict(config_sha256=identity(cfg),preparation=cfg['preparation'],
        # trainer_commit=commit,world_size=world_size) with commit=authenticate(cfg), world_size=recipe_for(cfg)[...]
        bound = dict(config_sha256=run.identity(job), preparation=job['preparation'],
                     trainer_commit=run.authenticate(job), world_size=recipe_for(job)['world_size'])
        result['bound'] = bound
        output = Path(job['output'])
        counts = dict(pose=9, vqa=9, pointing=9)
        base = dict(base_identity='fixture', trace_program_version='3.13',
                    checkpoint_disk_guard=job['checkpoint_disk_guard'])

        def build():
            model, _, _ = fixture(4)
            wrapped = run.wrap_model(model, torch.device('cpu'), mixed_precision=False)
            optimizer = torch.optim.AdamW(parameter_groups(wrapped), weight_decay=.01)
            return model, wrapped, optimizer

        def steps_run(model, wrapped, optimizer, out_dir, cfg, start):
            return run.run_steps(model, wrapped, optimizer, FixtureRows(), counts, out_dir, cfg, bound,
                                 torch.device('cpu'), rank, start, None, None, [False], distributed=True)

        def persist(directory, kind):
            t = time.time()
            persistence.milestone(job, directory, kind, rank, True)
            return round(time.time() - t, 3)

        if phase == 'A':
            model, wrapped, optimizer = build(); seed()
            if rank == 0:
                output.mkdir(parents=True, exist_ok=True)
                run.bind_output(output, bound)
                write(output / f"attempt_{os.environ['SLURM_JOB_ID']}.json", dict(binding=bound, resume=None, first_step=1))
            dist.barrier()
            cfg = dict(base, recipe=dict(resume_every_seconds=0.001), stop_after_step=2)
            report = steps_run(model, wrapped, optimizer, output, cfg, 0)
            result['report'] = dict(last_step=report['last_step'], stop_reason=report['stop_reason'])
            pin = [run.latest_resume(output, bound) if rank == 0 else None]
            dist.broadcast_object_list(pin, src=0)
            result['newest'] = pin[0]
            result['persist_seconds'] = persist(Path(pin[0]['path']).parent, 'checkpoint')
            result['digest_step2'] = digests(wrapped)
            # control: the same init, uninterrupted to step 3, its own output (only the parameters are compared)
            model, wrapped, optimizer = build(); seed()
            control = NS / 'control'
            if rank == 0:
                control.mkdir(parents=True, exist_ok=True); run.bind_output(control, bound)
            dist.barrier()
            report = steps_run(model, wrapped, optimizer, control,
                               dict(base, recipe=dict(resume_every_seconds=0.001), stop_after_step=3), 0)
            result['control'] = dict(last_step=report['last_step'], digest_step3=digests(wrapped))
        else:
            model, wrapped, optimizer = build()      # no seed(): restore() sets every RNG from the state
            foreign = dict(bound, preparation=dict(bound['preparation'], sha256='0' * 64))
            if rank == 0:
                try:
                    run.latest_resume(output, foreign); result['refuse_latest_foreign'] = 'NOT REFUSED'
                except ValueError as e:
                    result['refuse_latest_foreign'] = str(e)
            pin = [run.latest_resume(output, bound) if rank == 0 else None]
            dist.broadcast_object_list(pin, src=0)
            try:
                run.restore(pin[0], wrapped, optimizer, foreign); result['refuse_restore_foreign'] = 'NOT REFUSED'
            except ValueError as e:
                result['refuse_restore_foreign'] = str(e)
            t = time.time()
            start = run.restore(pin[0], wrapped, optimizer, bound)
            result.update(loaded_pin=pin[0], loaded_step=start, restore_seconds=round(time.time() - t, 3),
                          digest_loaded=digests(wrapped))
            if rank == 0:
                try:
                    run.bind_output(output, bound); result['refuse_fresh_start'] = 'NOT REFUSED'
                except ValueError as e:
                    result['refuse_fresh_start'] = str(e)
                run.bind_output(output, bound, resume=True)
                write(output / f"attempt_{os.environ['SLURM_JOB_ID']}.json", dict(binding=bound, resume=pin[0], first_step=start + 1))
            dist.barrier()
            report = steps_run(model, wrapped, optimizer, output,
                               dict(base, recipe=dict(resume_every_seconds=7200), stop_after_step=3), start)
            result['report'] = dict(first_step=report['first_step'], last_step=report['last_step'],
                                    stop_reason=report['stop_reason'])
            newest = [run.latest_resume(output, bound) if rank == 0 else None]
            dist.broadcast_object_list(newest, src=0)
            result['saved'] = newest[0]
            result['saved_step'] = load(newest[0]['path'])['step']
            result['persist_checkpoint_seconds'] = persist(Path(newest[0]['path']).parent, 'checkpoint')
            result['persist_export_seconds'] = persist(output / 'm3', 'export')
            result['digest_step3'] = digests(wrapped)
            if rank == 0:
                rows = [json.loads(l) for l in (output / f"metrics_{os.environ['SLURM_JOB_ID']}.jsonl").read_text().splitlines()]
                result['metrics'] = [dict(step=r['step'], stream_means=r['ranks'][0].get('stream_means'),
                                          components=r['ranks'][0].get('components')) for r in rows]
                result['states'] = [str(p) for p in run.complete_states(output, bound)]
                result['export'] = file_pin(output / 'm3/artifact.json')
                result['persist'] = sorted(p.name for p in (output / 'persist').iterdir())
        result['status'] = 'PASS'
    except BaseException as e:
        result.update(status='FAIL', error=f'{type(e).__name__}: {e}', traceback=traceback.format_exc()[-6000:])
        raise
    finally:
        (out / f'{phase}_rank{rank}.json').write_text(json.dumps(result, indent=1, default=str) + '\n')
        dist.destroy_process_group()


def audit(event, arguments):
    # Nothing is removed except library temporary files under the run's tmp folder.
    if event in ('os.remove', 'os.rmdir', 'os.unlink', 'shutil.rmtree'):
        path = Path(os.fsdecode(arguments[0])).absolute()
        if not path.is_relative_to(NS / 'tmp'):
            raise PermissionError('The test retains its artifacts: ' + str(path))


if __name__ == '__main__':
    from tests.retained_workers import run_workers
    out.mkdir(parents=True, exist_ok=True)
    run_workers(worker, (), world=WORLD, timeout=900, start_method='fork')
    print('workers done', phase)

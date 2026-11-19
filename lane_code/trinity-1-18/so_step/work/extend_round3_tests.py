from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for name in ('test_round3_kits.py','test_round2_kits.py','test_kit_utilities.py'):
    p=ROOT/'work'/name;s=p.read_text().replace("dict(training_mode='final',r1_training=True)","dict(training_mode='final',r1_training={'fixture':True})");p.write_text(s)
p=ROOT/'work/test_round3_kits.py';s=p.read_text();mark="    def test_replay_mode_is_one_step_and_wrapper_is_off_off_on(self):"
s=s.replace(mark,'''    def test_full_replay_gate_binds_audit_plan_and_on_provenance(self):
        from replay_compare import compare, replay_order
        directory = root(); audit_dir = directory/'audit'; audit_dir.mkdir()
        for rank in range(4):
            for name,arm in replay_order():
                path=directory/name/f'rank{rank}'; path.mkdir(parents=True)
                values={'C1_CPU_PREFETCH':'1' if arm == 'prefetch' else '0',
                        'C1_BATCH_METRICS':'0','C1_DECODED_CACHE_MIB':'0','C1_CPU_PREFETCH_FALLBACK':'0'}
                meta=dict(arm=arm,start_step=200,resume={'pin':'same'},trainables=['same'],
                          config_sha256='cfg',binding={},threads={},switches=values)
                record=dict(step=201,plan_sha256='same',components={'a':1.},stream_means={'vqa':1.},
                            first_step_micro_losses=[1.])
                if arm == 'prefetch':
                    record['performance']=values
                (path/'manifest.json').write_text(json.dumps(meta))
                (path/'steps.json').write_text(json.dumps([record]))
                (path/'progress.json').write_text(json.dumps({'stage':'complete'}))
            for arm in ('off','prefetch'):
                path=audit_dir/f'data_{arm}_rank{rank}.json'
                record=dict(plan_sha256='same',row_draws=[['pose',0,0]],encoded_row_sha256=['same'],global_rng_unchanged=True)
                path.write_text(json.dumps([record]*10))
                meta=dict(start_step=200,resume={'pin':'same'},config_sha256='cfg',rank=rank,world_size=4,
                          plans_checked=10,coverage_required=True,augmented_pose_rows=1,
                          peak_group_tensor_bytes=100,group_budget_bytes=1024)
                Path(str(path)+'.manifest.json').write_text(json.dumps(meta))
        self.assertTrue(compare(directory,audit_dir)['accepted'])
        path=directory/'on/rank3/steps.json'
        good=path.read_text(); records=json.loads(good); records[0].pop('performance')
        path.write_text(json.dumps(records))
        with self.assertRaisesRegex(ValueError,'provenance'):
            compare(directory,audit_dir)
        path.write_text(good)
        path=audit_dir/'data_prefetch_rank3.json'; records=json.loads(path.read_text())
        records[0]['plan_sha256']='wrong'; path.write_text(json.dumps(records))
        with self.assertRaisesRegex(ValueError,'CPU audit'):
            compare(directory,audit_dir)

'''+mark);p.write_text(s)
p=ROOT/'work/b21_final/work/tree_r1/tests/test_so_round3.py';s=p.read_text()
s=s.replace('import os\n','import os\nimport json\nfrom pathlib import Path\nfrom types import SimpleNamespace\n')
pos=s.index('\n\nclass Round3')
s=s[:pos]+'''

def fallback_worker(rank, directory):
    import torch.distributed as dist
    from tests.so_helpers import assert_nested
    torch.set_num_threads(8)
    directory = Path(directory)
    dist.init_process_group('gloo',init_method='file://'+str(directory/'fallback_rendezvous'),rank=rank,world_size=2)
    try:
        receipt=json.loads((directory/'receipt.json').read_text())
        model=SimpleNamespace(recipe={'world_size':2,'reference_world_size':4},
                              training_mode='final',r1_training=True,frame_count=32)
        original_get, original_reduce = run.Rows.get, dist.all_reduce
        for failure in (False, True):
            results=[]
            for enabled in ('0','1'):
                collectives=[]; values=[]; error=None
                def get(rows, stream, index):
                    if failure and rank == 1 and stream == 'vqa' and index == 3:
                        raise ValueError('planted fallback admission failure')
                    return original_get(rows,stream,index)
                def reduce(flag,*args,**kwargs):
                    assert threading.current_thread() is threading.main_thread()
                    collectives.append((str(kwargs.get('op')),flag.tolist()))
                    return original_reduce(flag,*args,**kwargs)
                with patch.dict(os.environ,C1_CPU_PREFETCH=enabled,C1_CPU_PREFETCH_FALLBACK=enabled), \\
                        patch.object(prefetch,'MAX_GROUP_TENSOR_BYTES',1 if rank == 1 else 1<<30), \\
                        patch.object(run.Rows,'get',get),patch.object(dist,'all_reduce',reduce):
                    rows=run.Rows(receipt,compact_processor())
                    iterator=run.fetch_plan(rows,model,plan(2),rank,distributed=True)
                    try:
                        values.extend(iterator)
                    except ValueError as exc:
                        error=str(exc)
                    finally:
                        iterator.close();rows.close()
                if enabled == '1':
                    assert getattr(rows,'_c1_budget_fallback_groups',0) == ((2 if failure else 4) if rank == 1 else 0)
                results.append((values,collectives,error))
            assert_nested(unittest.TestCase(),*results)
            assert (results[0][2] is not None) == failure
        (directory/f'fallback_rank{rank}.json').write_text(json.dumps({'rank':rank,'status':'PASS'}))
    finally:
        dist.destroy_process_group()
'''+s[pos:]
s=s.replace('    def test_export_leg_has_docstring(self):', '''    def test_two_rank_budget_fallback_keeps_values_and_admission(self):
        import torch.multiprocessing as mp
        directory=root()
        (directory/'receipt.json').write_text(json.dumps(inputs(directory)))
        mp.spawn(fallback_worker,args=(str(directory),),nprocs=2,join=True)
        self.assertEqual([json.loads((directory/f'fallback_rank{r}.json').read_text())['status'] for r in range(2)],['PASS','PASS'])
        print('SO_FALLBACK_PROOF rank1-only over-budget fallback; exact rows and collective sequence; both ranks raise in the same group',flush=True)

    def test_export_leg_has_docstring(self):''')
p.write_text(s)

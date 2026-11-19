from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'out/kit_timing/data_only.py'; s=p.read_text()
s=s.replace('import random\n','import random\nimport resource\n')
s=s.replace('\ndef main():', '''
def descriptor_for(run, cfg, receipt):
    descriptor = SimpleNamespace(recipe=run.recipe_for(cfg), training_mode=cfg.get('training_mode','final'),
        frame_count=cfg.get('frame_count',32), geometry_online=cfg.get('geometry_online'),
        r1_training=cfg.get('r1_training'))
    if cfg.get('align') != receipt.get('align'):
        raise ValueError('Configuration and receipt alignment differ')
    if receipt.get('align'):
        descriptor.align_settings = receipt['align']
    return descriptor


def main():''')
s=s.replace("help='off/rank0/plan.json from the production comparison'", "help='Bounded continuation plan from write_plan.py'")
s=s.replace("help='Audit every supplied epoch plan; no 100-step cap'", "help='Audit every supplied plan (normally the bounded 10-update plan)'")
s=s.replace("    parser.add_argument('--gpu-copy'", "    parser.add_argument('--require-coverage',action='store_true',help='Require actual augmented pose rows and capped processor grids')\n    parser.add_argument('--gpu-copy'")
s=s.replace("C1_BATCH_METRICS='0')", "C1_BATCH_METRICS='0', C1_CPU_PREFETCH_FALLBACK='0')")
a=s.index('    processor=run.processor_for_receipt('); b=s.index("    if cfg.get('geometry_online')",a)
s=s[:a]+'''    receipt = run.load(args.receipt)
    processor=run.processor_for_receipt(run.load(args.manifest),receipt)
    descriptor=descriptor_for(run,cfg,receipt)
'''+s[b:]
s=s.replace("    if args.full_plan:\n", """    if frozen.get('config_sha256',run.identity(cfg)) != run.identity(cfg):
        raise ValueError('Audit plan configuration differs')
    if frozen.get('receipt_sha256',run.file_pin(args.receipt)['sha256']) != run.file_pin(args.receipt)['sha256']:
        raise ValueError('Audit plan receipt differs')
    if args.full_plan:
""")
s=s.replace('    rows=run.Rows(run.load(args.receipt),processor)\n    result=[]\n    try:', '''    rows=run.Rows(receipt,processor)
    from audit import Coverage
    from student_pilot import pose_samples
    coverage = Coverage()
    augmentation = coverage.augmentation(pose_samples)
    augmentation.__enter__()
    result=[]
    try:''')
s=s.replace("enumerate(frozen['plans'][:args.steps],1)", "enumerate(frozen['plans'][:args.steps],frozen.get('start_step',0)+1)")
s=s.replace("                draws.append([stream,", "                coverage.observe(batch)\n                draws.append([stream,")
s=s.replace('    finally:\n        rows.close()', '    finally:\n        rows.close()\n        augmentation.__exit__(None,None,None)')
s=s.replace('        peak_group_tensor_bytes=peak,', '''        start_step=frozen.get('start_step',0), resume=frozen.get('resume'),
        plan_sha256=run.file_pin(args.plan)['sha256'],
        peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
        augmented_pose_rows=coverage.augmented_pose_rows, augmentation_threads=sorted(coverage.augmentation_threads),
        grid_cap=[32,20,26], observed_max_grid=coverage.max_grid, grid_rows=coverage.grid_rows,
        coverage_required=args.require_coverage,
        peak_group_tensor_bytes=peak,''')
s=s.replace('    if args.baseline:\n', "    if args.require_coverage:\n        coverage.require(prefetch=args.arm in ('prefetch','all'))\n    if args.baseline:\n")
s=s.replace("raise ValueError('Full group tensor budget", "raise ValueError('Prepared group tensor budget")
p.write_text(s)
p=ROOT/'out/kit_profile/launch.py';s=p.read_text()
s=s.replace("choices=('profile', 'timing')", "choices=('profile', 'timing', 'replay')")
s=s.replace("    parser.add_argument('--profile-microsteps'", "    parser.add_argument('--batch-metrics', choices=('0','1'), default='0', help='Hold 03 constant across acceptance replays')\n    parser.add_argument('--profile-microsteps'")
s=s.replace("'C1_BATCH_METRICS': '0'}", "'C1_BATCH_METRICS': args.batch_metrics, 'C1_CPU_PREFETCH_FALLBACK': '0'}")
s=s.replace("    if args.mode == 'timing' and args.arm != 'off' and not args.plan:", "    if args.mode == 'replay' and (not args.resume or not args.plan):\n        parser.error('Replay requires --resume and the CPU-audited --plan')\n    if args.mode == 'timing' and args.arm != 'off' and not args.plan:")
s=s.replace("args.mode == 'profile' or index >= args.warmup", "args.mode != 'timing' or index >= args.warmup")
s=s.replace("            if 'decoded_cache' in info:", "            if 'performance' in info:\n                record['performance'] = info['performance']\n            if 'decoded_cache' in info:")
p.write_text(s)
# Keep the startup transport mocked but stop exposing mock CUDA availability to CPU AdamW.
p=ROOT/'work/b21_final/work/tree_r1/tests/test_so_round3.py';s=p.read_text()
s=s.replace("            records.append(run.optimize_step(model, optimizer, rows, plan(), 0, torch.device('cpu'), 1)[0])", "            with patch.object(torch.cuda, 'is_available', return_value=False):\n                records.append(run.optimize_step(model, optimizer, rows, plan(), 0, torch.device('cpu'), 1)[0])")
p.write_text(s)

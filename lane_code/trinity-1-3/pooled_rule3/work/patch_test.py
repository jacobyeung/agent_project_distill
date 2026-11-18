p = 'test_pooled_rule_v3.py'
s = open(p).read()
old = s[s.index('    def test_one_read_per_boundary_and_arm(self):'):s.index('def synthetic(')]
new = '''    def test_one_read_per_boundary_and_arm(self):
        lg = os.path.join(TMP, 'ledger.jsonl')
        e = dict(kind='decision', step=200, arm='direct', set='dev-S1', run_id='673bc60f', artifact_sha256='f' * 64,
                 read_sha256='a' * 64, manifest_sha256='b' * 64)
        self.assertTrue(RULE.ledger_check(lg, e))
        with open(lg, 'a') as f:
            f.write(json.dumps(e) + '\\n')
        self.assertFalse(RULE.ledger_check(lg, dict(e)))                          # the same read again: accepted, not logged twice
        with self.assertRaises(RULE.Refused):
            RULE.ledger_check(lg, dict(e, read_sha256='c' * 64))                    # a second, different read of the boundary
        with self.assertRaises(RULE.Refused):
            RULE.ledger_check(lg, dict(e, manifest_sha256='d' * 64))
        self.assertTrue(RULE.ledger_check(lg, dict(e, step=400, read_sha256='c' * 64, artifact_sha256='9' * 64)))


INVENTED = 'e' * 64


def constructed():
    """The reviewer's case: D0 m200's read relabelled as R1 step 200 with an invented artifact, its archive omitted, and
    checksum-valid receipts whose bindings are empty."""
    m = man('D0m200')
    for d in 'SR':
        r = m[d]['run']
        r.update(run_id='673bc60f', artifact_sha256=INVENTED, artifact_path=r['artifact_path'].replace('/runs/359fcc3c/', '/runs/673bc60f/'))
        m[d]['read_file'].pop('archive')
        for rc in m[d]['receipts']:
            rc['binds'] = []
    return m


def base_ctx(d):
    b = RULE.BASE[d]
    xw = json.load(open(RULE.CROSSWALK))
    return json.load(open(b['manifest'])), json.load(open(xw['sources']['id_map']['path']))


def receipt(run, step, obj):
    d = os.path.join(TMP, 'runs', run, 'm%d' % step)
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, 'artifact.json')
    with open(p, 'w') as f:
        json.dump(obj, f, sort_keys=True)
    return p


class ReviewerCase(unittest.TestCase):
    """Each of the four provenance points refuses the reviewer's constructed case on its own."""
    def check(self, m, d='S'):
        base_m, idm = base_ctx(d)
        reads = {RULE.sha(p): p for p in READS['D0m200']}
        with self.assertRaises(RULE.Refused) as e:
            RULE.check_manifest(m[d], d, reads, base_m, idm)
        return str(e.exception)

    def test_whole_case_refused(self):
        for calibration in (False, True):
            with self.assertRaises(RULE.Refused):
                RULE.prepare(READS['D0m200'], constructed(), 200, calibration,
                             export_receipt=receipt('673bc60f', 200, dict(schema='carrier-c1-artifact-v1', step=200)))

    def test_point1_omitted_archive(self):
        for d in 'SR':
            self.assertIn('names no fetched archive', self.check(constructed(), d))
        m = man('D0m200')                                                         # the archive alone omitted from a real manifest
        m['S']['read_file'].pop('archive')
        with self.assertRaises(RULE.Refused) as e:
            RULE.prepare(READS['D0m200'], m, 200, True)
        self.assertIn('names no fetched archive', str(e.exception))

    def test_point1b_archive_content_differs(self):
        m = man('D0m200')
        m['S']['read_file']['archive'] = dict(m['R']['read_file']['archive'])   # a real archive of another read
        with self.assertRaises(RULE.Refused) as e:
            RULE.prepare(READS['D0m200'], m, 200, True)
        self.assertIn('not the decoded ITEMS.jsonl of the fetched archive', str(e.exception))

    def test_point2_empty_bindings(self):
        for d in 'SR':
            m = constructed()
            m[d]['read_file']['archive'] = man('D0m200')[d]['read_file']['archive']    # isolate: archive restored
            self.assertIn('binds no field', self.check(m, d))
        m = man('D0m200')                                                         # the empty bindings alone, in a real manifest
        m['R']['receipts'][0]['binds'] = []
        with self.assertRaises(RULE.Refused) as e:
            RULE.prepare(READS['D0m200'], m, 200, True)
        self.assertIn('binds no field', str(e.exception))

    def test_point2b_each_required_binding(self):
        for f in RULE.RUN_BINDS + (RULE.ARCHIVE_BIND,):
            for d in 'SR':
                m = man('D0m200')
                rcs = []
                for rc in m[d]['receipts']:
                    rc['binds'] = [x for x in rc['binds'] if x[1] != f]
                    if rc['binds']:
                        rcs.append(rc)
                m[d]['receipts'] = rcs
                with self.assertRaises(RULE.Refused) as e:
                    RULE.prepare(READS['D0m200'], m, 200, True)
                self.assertIn('no receipt binds %s' % f, str(e.exception), (f, d))

    def test_point3_invented_artifact(self):
        run = constructed()['S']['run']
        with self.assertRaises(RULE.Refused) as e:                                # the run's real receipt registers another artifact
            RULE.check_export_receipt(run, receipt('673bc60f', 200, dict(schema='carrier-c1-artifact-v1', step=200)))
        self.assertIn('is not the one the training run registers', str(e.exception))
        for p in (None, os.path.join(TMP, 'absent.json')):
            with self.assertRaises(RULE.Refused):
                RULE.check_export_receipt(run, p)
        p = receipt('673bc60f', 200, dict(schema='carrier-c1-artifact-v1', step=400))  # right bytes, wrong step
        with self.assertRaises(RULE.Refused):
            RULE.check_export_receipt(dict(run, artifact_sha256=RULE.sha(p)), p)
        p = receipt('359fcc3c', 200, dict(schema='carrier-c1-artifact-v1', step=200))  # another run's receipt
        with self.assertRaises(RULE.Refused):
            RULE.check_export_receipt(dict(run, artifact_sha256=RULE.sha(p)), p)
        good = receipt('673bc60f', 200, dict(schema='carrier-c1-artifact-v1', step=200, note='r1'))
        RULE.check_export_receipt(dict(run, artifact_sha256=RULE.sha(good)), good)    # the matching receipt passes
        with self.assertRaises(RULE.Refused) as e:                                # alone, on a real manifest: receipt of another export
            RULE.prepare(READS['D0m200'], man('D0m200'), 200, True, export_receipt=receipt('359fcc3c', 200, dict(step=200)))
        self.assertIn('is not the one the training run registers', str(e.exception))

    def test_point4_read_hash_recorded_elsewhere(self):
        m = constructed()
        for d in 'SR':
            e = dict(kind='decision', step=200, arm='direct', set=RULE.BASE[d]['name'], run_id='673bc60f', artifact_sha256='1' * 64,
                     read_sha256=m[d]['read_file']['sha256'], manifest_sha256='b' * 64)
            with self.assertRaises(RULE.Refused) as x:                            # the tool's prior reads hold D0 m200's read
                RULE.ledger_check(None, e)
            self.assertIn('already recorded under run 359fcc3c step 200', str(x.exception))
        lg = os.path.join(TMP, 'ledger4.jsonl')                                   # a read first recorded in the ledger
        e = dict(kind='calibration', step=200, arm='direct', set='dev-S1', run_id='aaaa0001', artifact_sha256='2' * 64,
                 read_sha256='3' * 64, manifest_sha256='4' * 64)
        self.assertTrue(RULE.ledger_check(lg, e))
        with open(lg, 'a') as f:
            f.write(json.dumps(e) + '\\n')
        for change in (dict(run_id='673bc60f', kind='decision'), dict(step=400)):
            with self.assertRaises(RULE.Refused):
                RULE.ledger_check(lg, dict(e, artifact_sha256='5' * 64, **change))
        with self.assertRaises(RULE.Refused):                                     # an export recorded elsewhere
            RULE.ledger_check(lg, dict(e, run_id='673bc60f', kind='decision', read_sha256='6' * 64))

    def test_decision_cli_requires_receipt_and_ledger(self):
        out = subprocess.run([sys.executable, os.path.join(HERE, 'pooled_harm_rule_v3.py'), '--step', '200', '--read'] + READS['D0m200'] +
                             ['--manifest-s1', put('ms.json', man('D0m200')['S']), '--manifest-r0', put('mr.json', man('D0m200')['R']),
                              '--output', os.path.join(TMP, 'o.json'), '--ledger', os.path.join(TMP, 'l.jsonl')],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        self.assertNotEqual(out.returncode, 0)
        self.assertIn('--export-receipt', out.stderr)


class Baselines(unittest.TestCase):
    def test_two_real_baseline_manifests_pass(self):
        for d in 'SR':
            base_m, idm = base_ctx(d)
            b = RULE.BASE[d]
            self.assertEqual(RULE.check_manifest(base_m, d, {b['sha256']: b['path']}, base_m, idm, baseline=True), b['path'])
            bound = {x[1] for rc in base_m['receipts'] for x in rc['binds']}
            self.assertTrue(set(RULE.RUN_BINDS) <= bound, d)

    def test_three_real_reads_object_size_intervals(self):
        want = dict(D0m200=([-10.641, -1.668], [-11.148, -1.208]), D0m100=([-8.345, -0.967], [-8.947, -0.588]),
                    H1m100=([-8.326, -0.711], [-9.279, -0.275]))
        for arm, (i200, later) in want.items():
            data = RULE.prepare(READS[arm], man(arm), 200, True)
            for step, iv in ((200, i200), (400, later)):
                r = RULE.display(RULE.decide(data, step))
                row = next(t for t in r['types'] if t['type'] == 'object_size_estimation')
                self.assertEqual(row['interval_pp'], iv, (arm, step))
                self.assertTrue(row['fires'])


'''
s = s.replace(old, new)
open(p, 'w').write(s)

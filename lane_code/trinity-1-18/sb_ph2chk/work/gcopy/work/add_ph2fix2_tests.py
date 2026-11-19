from pathlib import Path
p=Path('sb_mask_phrase/part2/test_part2.py');s=p.read_text().replace('import numpy as np','import numpy as np\nfrom unittest.mock import patch')
idx=s.index('\n\nclass Admission')
s=s[:idx]+'''
    def test_decision_fixture_reproduces_W1_1012(self):
        files = sorted((K.WORK/'part2_fixture/caps').glob('*.json.gz'))
        data = [AG.gz(p) for p in files]
        part1 = json.loads(P.T.read(K.OUT/'DECISION.json'))
        a0 = json.loads(P.T.read(K.WORK/'A0_ROWS.json'))['rows']['A0_deployed']
        wcf = [json.loads(line) for line in P.T.read(K.OUT/'PER_ITEM.jsonl').decode().splitlines()]
        wcf = [r for r in wcf if r['arm'] == 'W1']
        result, arms = P.population(data, wcf, a0, lambda c: c not in AG.WITHHELD, part1['fold_choices']['W1'])
        self.assertEqual((result['rows'], result['captures'], result['both_good_rows']), (1012, 204, 442))
        gain = result['arms']['W_exact']['gain']
        self.assertEqual(round(gain['estimate'], 2), 3.82)
        self.assertEqual([round(v, 2) for v in gain['ci95']], [2.16, 5.63])
        self.assertEqual(result['w_exact_rows_equal_w_cf'], 1012)
        self.assertTrue(all(r['capture'] not in AG.WITHHELD for rows in arms.values() for r in rows))
        # Every fitted object must come from the kept captures, including all-room fits.
        expected = sum(len(d['names']) for d in data if d['capture'] not in AG.WITHHELD)
        seen = []
        original = AG.choose
        def choose(objects, candidates, fold):
            if fold is None:
                seen.extend(objects)
            return original(objects, candidates, fold)
        with patch.object(AG, 'choose', choose), patch.object(AG, 'arm_report', return_value={}):
            P.population(data, wcf, a0, lambda c: c not in AG.WITHHELD, part1['fold_choices']['W1'])
        self.assertEqual(len(seen), expected)

    def test_price_outputs_are_exclusive(self):
        root = Path(tempfile.mkdtemp(dir=K.WORK))
        for name, writer in [('score.json', P.write_json), ('score.json.gz', P.write_gz)]:
            p = root/name
            p.write_bytes(b'preserve')
            with self.assertRaises(FileExistsError): writer(p, {})
            self.assertEqual(p.read_bytes(), b'preserve')
            link = root/('dangling_'+name)
            target = root/('target_'+name)
            link.symlink_to(target)
            with self.assertRaises(FileExistsError): writer(link, {})
            self.assertFalse(target.exists())
''' +s[idx:]
s=s.replace("            if condition == 'capture_work':", '''            if condition in ('dangling_symlink', 'dir_symlink', 'upper_JSON', 'csv_scores'):
                folder = root/'out/part2'
                folder.mkdir(parents=True)
                if condition == 'dangling_symlink':
                    (folder/'PER_ITEM_PART2.jsonl').symlink_to(root/'absent.jsonl')
                elif condition == 'dir_symlink':
                    target = root/'elsewhere'; target.mkdir()
                    (target/'score.json').write_text('{}')
                    (folder/'linked').symlink_to(target, target_is_directory=True)
                else:
                    (folder/('scores.JSON' if condition == 'upper_JSON' else 'scores.csv')).write_text('{}')
            if condition == 'capture_work':''')
s=s.replace("(K.sha(p) if p.is_file() else 'DIRECTORY', p.stat().st_mtime_ns)", "(os.readlink(p) if p.is_symlink() else K.sha(p) if p.is_file() else 'DIRECTORY', p.lstat().st_mtime_ns)")
s=s.replace("    def test_planted_per_item_refused_without_writes(self):", '''    def test_dangling_symlink_refused_without_writes(self):
        self.exercise('dangling_symlink')

    def test_directory_symlink_refused_without_writes(self):
        self.exercise('dir_symlink')

    def test_uppercase_score_refused_without_writes(self):
        self.exercise('upper_JSON')

    def test_csv_score_refused_without_writes(self):
        self.exercise('csv_scores')

    def test_planted_per_item_refused_without_writes(self):''')
s=s.replace("input_sha256={str(p): K.sha(p) for p in [", "input_sha256=dict(P.T.PINS, **{str(p): K.sha(p) for p in [")
s=s.replace("K.WORK/'part2_fixture/aggregate/DECISION_PART2.json']}),", "K.WORK/'part2_fixture/aggregate/DECISION_PART2.json']})),")
p.write_text(s)
p=Path('sb_mask_phrase/part2/test_launcher.py');s=p.read_text().replace('import os\n','import os\nimport re\n')
s=s.replace('class Launcher(unittest.TestCase):', '''def allowed_write(path, out, user):
    path = Path(path)
    return path.is_relative_to(out) or re.fullmatch(r'/tmp/terminator/' + re.escape(user) + r'-[0-9]+', str(path)) is not None


class Launcher(unittest.TestCase):''')
s=s.replace('self.assertTrue(p.is_relative_to(self.out),str(p))', "self.assertTrue(allowed_write(p, self.out, os.environ['USER']),str(p))")
s=s.replace("    def test_complete_pass_never_relaunched(self):", '''    def test_only_terminator_control_allowed_outside_pool(self):
        user = os.environ['USER']
        self.assertTrue(allowed_write(f'/tmp/terminator/{user}-123', self.out, user))
        for path in ('/tmp/terminator/other-123', f'/tmp/terminator/{user}-abc',
                     f'/tmp/terminator/{user}-123/nested', '/tmp/other', '/home/test'):
            self.assertFalse(allowed_write(path, self.out, user), path)
        vendor = L.KIT/'part2/vendor'
        self.assertEqual(L.sha(vendor/'terminator.sh'), '19727987d5517c0e2549e1205e55f4bcc87f34dafe66c96bdf90233305942e5d')
        self.assertEqual(json.loads((vendor/'PINS.json').read_text())['sha256']['terminator.sh'], L.sha(vendor/'terminator.sh'))

    def test_environment_confines_openssl_and_path(self):
        env = L.environment(self.kit, self.out, 'GPU-test', 4320, 'pass', False)
        self.assertEqual(env['PATH'], '/usr/bin:/bin')
        self.assertEqual(env['OPENSSL_CONF'], str(self.kit.parent/'payload/environment/ssl/openssl.cnf'))

    def test_complete_pass_never_relaunched(self):''')
s=s.replace("L.KIT/'part2/sam3_pass.py']", "L.KIT/'part2/sam3_pass.py', L.KIT/'part2/vendor/PINS.json', L.KIT/'part2/vendor/terminator.sh', L.KIT/'part2/launch_gpu.sh']")
p.write_text(s)
p=Path('verify_cpu.py');s=p.read_text().replace('ph2fix_verified','ph2fix2_verified').replace("t2['ran'] == 20", "t2['ran'] == 26").replace("agg['w_exact_rows_equal_w_cf'] == 1037", "agg['w_exact_rows_equal_w_cf'] == 1012 and agg['w_exact_rows_equal_w_cf_1037'] == 1037")
p.write_text(s)

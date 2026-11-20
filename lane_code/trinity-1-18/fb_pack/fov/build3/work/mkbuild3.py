"""build3 = build2 score_fov.py + adapter for the producer's FOV_CHECK.json row fields (fov_check.py 762093b8)."""
import hashlib, pathlib, shutil, sys
F = pathlib.Path('/scratch/jjyeung/orch_n30/fb_pack/fov')
src, dst = F / 'build2/score_fov.py', F / 'build3/score_fov.py'
(F / 'build3').mkdir(exist_ok=True)
assert not dst.exists()
s = src.read_text()
a = """    if 'grid_uv' in row:
        value = np.asarray(row['grid_uv'])
        if value.shape != grid.shape or not np.array_equal(value, grid):
            fail('P3_GRID_UV', label + '.grid_uv')
        evidence.append('grid_uv values')
"""
b = """    if row.get('scored') is not True:
        fail('P3_ROW_NOT_SCORED', label + '.scored must be true')
    for flag in ('capture_sha256_equal', 'receipt_ok'):
        if row.get(flag) is not True:
            fail('P3_ROW_' + flag.upper(), label + '.' + flag + ' must be true')
    if row.get('second_pass_max_abs') != 0.0:
        fail('P1_ROW_SECOND_PASS', label + '.second_pass_max_abs must be 0.0')
    if 'grid_uv' in row and isinstance(row['grid_uv'], str):
        # Producer fov_check.py 762093b8 writes grid_uv as sha256 of the float32 GRID_UV bytes.
        if row['grid_uv'] != hashlib.sha256(grid.tobytes()).hexdigest():
            fail('P3_GRID_UV_SHA256', label + '.grid_uv')
        evidence.append('grid_uv sha256 string (fov_check 762093b8)')
    elif 'grid_uv' in row:
        value = np.asarray(row['grid_uv'])
        if value.shape != grid.shape or not np.array_equal(value, grid):
            fail('P3_GRID_UV', label + '.grid_uv')
        evidence.append('grid_uv values')
"""
assert s.count(a) == 1
dst.write_text(s.replace(a, b))
for d in ('tests',):
    if (F / 'build2' / d).is_dir() and not (F / 'build3' / d).exists():
        shutil.copytree(F / 'build2' / d, F / 'build3' / d)
print('build2', hashlib.sha256(src.read_bytes()).hexdigest())
print('build3', hashlib.sha256(dst.read_bytes()).hexdigest())

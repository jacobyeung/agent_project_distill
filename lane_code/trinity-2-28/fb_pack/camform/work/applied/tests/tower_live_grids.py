"""Reference checks for the live tower's frame-1 points and depth confidence."""
import numpy as np


def compare_auxiliary_grids(state, reference, tolerance):
    report = {}
    for name, shape in (('points_grid', (32, 51, 51, 3)),
                        ('depth_conf_grid', (32, 51, 51))):
        actual = np.asarray(getattr(state, name, None), dtype=float)
        expected = np.asarray(reference.get(name), dtype=float)
        row = dict(shape_ok=actual.shape == expected.shape == shape, passed=False)
        if row['shape_ok']:
            valid_a, valid_b = np.isfinite(actual), np.isfinite(expected)
            row['finite_pattern_equal'] = bool(np.array_equal(valid_a, valid_b))
            valid = valid_a & valid_b
            if name == 'points_grid':
                valid = valid.all(-1)
                delta = np.linalg.norm(actual[valid]-expected[valid], axis=-1)
                scale = np.linalg.norm(expected[valid], axis=-1)
            else:
                delta = np.abs(actual[valid]-expected[valid])
                scale = np.abs(expected[valid])
            row['compared_cells'] = int(valid.sum())
            if valid.any():
                relative = delta / np.maximum(scale, 1e-3)
                row.update(relative_error_median=float(np.median(relative)),
                           relative_error_p95=float(np.percentile(relative, 95)),
                           relative_error_max=float(relative.max()))
                row['passed'] = row['finite_pattern_equal'] and row['relative_error_median'] <= tolerance
        report[name] = row
    report['auxiliary_grids_pass'] = all(row['passed'] for row in report.values())
    return report

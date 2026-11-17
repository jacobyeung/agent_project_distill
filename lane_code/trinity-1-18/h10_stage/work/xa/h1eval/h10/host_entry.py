"""Resolve run-host settings without shell interpolation of JSON paths."""
import os
from .parity_adapter import settings_for


def main():
    env = os.environ
    name = 'revsi999' if env['H10_ITEMS'].endswith('/revsi999.json') else 'devs1_routed'
    settings = settings_for(env['H10_SETTINGS'], name)
    for field, var in (('export_dir', 'H10_EXPORT'), ('artifact_manifest', 'H10_ARTIFACT_MANIFEST')):
        if env.get(var) not in (None, 'from-settings', settings[field]):
            raise ValueError(var + ' differs from settings')
    args = ['--settings', env['H10_SETTINGS'], '--reader-root', env['H10_READER_ROOT'],
            '--items', env['H10_ITEMS'], '--export', settings['export_dir'],
            '--artifact-manifest', settings['artifact_manifest'], '--out', env['H10_OUT']]
    if env.get('H10_CPU_FIRST') == '1':
        from .cpu_first_batch import main as entry
    else:
        from .launch import main as entry
        arms = env['H10_ARMS']
        if env.get('H10_TOWER_FROM'):
            arms = 'own,tower'
            args += ['--tower-from', env['H10_TOWER_FROM']]
        args += ['--device','cuda:0','--shard',env['H10_SHARD'],'--arms',arms]
        if env.get('H10_MODES'):args += ['--modes',env['H10_MODES']]
        if env.get('H10_TYPES'):args += ['--types',env['H10_TYPES']]
    return entry(args)

if __name__ == '__main__':raise SystemExit(main())

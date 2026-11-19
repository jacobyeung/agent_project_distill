from pathlib import Path
Path('/project/n/o/94/live/probe').write_text('ok')
try:Path('/project/n/o/94/routing_selection.json').write_text('{}')
except OSError as e:assert e.errno==30
else:raise AssertionError('project is writable')

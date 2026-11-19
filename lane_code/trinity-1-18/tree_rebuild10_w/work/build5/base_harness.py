"""Keep the same policy; select only failing legacy cases for base comparison."""
from pathlib import Path
L=Path(__file__).resolve().parents[2]
target=L/'work/tmp/package/work/build5/test_runner.py'
target.write_bytes((L/'work/build5/test_runner.py').read_bytes())

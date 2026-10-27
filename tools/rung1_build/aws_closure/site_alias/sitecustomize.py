"""Adapt the frozen trainer's code-aws Slurm admission module to the live AWS controller.

Since 2026-10-20 22:13 PT the AWS job-submit plugin runs every pool0 request in pool0_datahall_a or
pool0_datahall_b, and the AWS controller sometimes answers ``scontrol show job`` after more than the
module's 30-second timeout. When the pinned admission module loads, by import or as ``python -m``, this
hook inserts the partition alias right after its SLURM_SITES table and rebinds ``command`` so that a
subprocess.TimeoutExpired is retried up to six times. Every query, parse and check stays unchanged.
"""
import ast
import hashlib
import importlib.abc
import importlib.machinery
import importlib.util
import sys

TARGET = "student_pilot.orchard_admission"
MODULE_SHA256 = "845cceec09a23663222740be82e50d4a5c556a6780568e8a23fbca793330c499"  # neutral trainer b4b2979 admission module
ALIASES = ("pool0_datahall_a", "pool0_datahall_b")
COMMAND_SOURCE = "def command(*args):\n    return subprocess.check_output(args, text=True, timeout=30).strip()"
RETRY_SOURCE = """
_aws_command_once = command
AWS_COMMAND_ATTEMPTS = 6
def command(*args):
    for _aws_attempt in range(AWS_COMMAND_ATTEMPTS):
        try:
            return _aws_command_once(*args)
        except subprocess.TimeoutExpired:
            if _aws_attempt + 1 == AWS_COMMAND_ATTEMPTS:
                raise
"""
ALIAS_SOURCE = """
_aws_partitions = SLURM_SITES["code-aws"]["partitions"]
if _aws_partitions != {"pool0": ({"av_alpamayo_aml_low", "av_alpamayo_aml_normal", "av_alpamayo_aml_high"}, 8)}:
    raise ImportError("The frozen code-aws partition table differs from its pinned value")
for _aws_alias in ("pool0_datahall_a", "pool0_datahall_b"):
    _aws_partitions[_aws_alias] = (set(_aws_partitions["pool0"][0]), 8)
AWS_PARTITION_ALIASES = ("pool0_datahall_a", "pool0_datahall_b")
del _aws_partitions, _aws_alias
"""


def aliased_code(data, path):
    if hashlib.sha256(data).hexdigest() != MODULE_SHA256:
        raise ImportError("The frozen Slurm admission module differs from its pinned bytes")
    tree = ast.parse(data, path)
    positions = [index for index, node in enumerate(tree.body) if isinstance(node, ast.Assign)
                 and [ast.unparse(target) for target in node.targets] == ["SLURM_SITES"]]
    if len(positions) != 1:
        raise ImportError("The frozen admission module must define SLURM_SITES exactly once")
    commands = [index for index, node in enumerate(tree.body) if isinstance(node, ast.FunctionDef) and node.name == "command"]
    if len(commands) != 1 or ast.unparse(tree.body[commands[0]]) != COMMAND_SOURCE or commands[0] < positions[0]:
        raise ImportError("The frozen admission module's command function differs from its pinned form")
    tree.body[commands[0] + 1:commands[0] + 1] = ast.parse(RETRY_SOURCE).body
    tree.body[positions[0] + 1:positions[0] + 1] = ast.parse(ALIAS_SOURCE).body
    return compile(ast.fix_missing_locations(tree), path, "exec", dont_inherit=True)


class AliasLoader(importlib.machinery.SourceFileLoader):
    def get_code(self, fullname):
        return aliased_code(self.get_data(self.path), self.path)


class AliasFinder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        if fullname != TARGET:
            return None
        for finder in sys.meta_path:
            if finder is self or not hasattr(finder, "find_spec"):
                continue
            spec = finder.find_spec(fullname, path, target)
            if spec is not None:
                break
        else:
            return None
        if not spec.origin or not spec.origin.endswith(".py"):
            raise ImportError("The frozen Slurm admission module has no source origin")
        return importlib.util.spec_from_file_location(fullname, spec.origin,
                                                      loader=AliasLoader(fullname, spec.origin))


if not any(isinstance(finder, AliasFinder) for finder in sys.meta_path):
    sys.meta_path.insert(0, AliasFinder())

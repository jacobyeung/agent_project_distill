"""Bind trace semantics to the model before its first tool response."""
from trace_format.program_errors import ProgramRefusal
KEY = 'trace_program_version'
def require(value):
    if value is None:raise ProgramRefusal('trace_program_version_missing')
    if value not in ('3.13','3.14'):raise ProgramRefusal('unsupported_program_version')
    return value
def resolve(artifact, config=None):
    config = config or {}
    saved = artifact.get(KEY)
    requested = config.get(KEY)
    if saved is None:
        if artifact.get('trace_version_binding'):
            raise ProgramRefusal('trace_program_version_missing')
        return require(requested)  # Pre-field exports require an explicit run setting.
    require(saved)
    if requested is not None and require(requested) != saved:
        raise ProgramRefusal('trace_program_version_mismatch')
    return saved
def bind(model, artifact, config=None):
    model.trace_program_version = resolve(artifact, config)
    return model.trace_program_version
def metadata(config):
    return {KEY: require(config.get(KEY)), 'trace_version_binding': 1}
def model_version(model, requested=None):
    return resolve({KEY:getattr(model,KEY,None)}, {KEY:requested} if requested else {})

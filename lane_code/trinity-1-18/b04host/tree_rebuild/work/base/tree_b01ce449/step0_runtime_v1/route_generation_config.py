def require_frozen_generation_config(native_config, processor, expected):
    from student_pilot.diagnostic import generation_config
    config = generation_config(native_config, processor, 4096)
    config.output_attentions = False
    config.output_hidden_states = False
    actual = config.to_dict()
    if actual != expected:
        differences = {key: {'expected': expected.get(key), 'actual': actual.get(key)} for key in sorted(set(actual) | set(expected)) if actual.get(key) != expected.get(key)}
        raise ValueError('Full effective generation configuration differs: ' + repr(differences))
    return config

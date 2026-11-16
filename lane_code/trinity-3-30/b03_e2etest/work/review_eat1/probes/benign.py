def print_native_head(value):
    # The head already predicts centimetres. This prints its output unchanged.
    return f'{value} cm'


def spatial_shape(frames):
    # An ordinary frame tensor shape, not a fitted parameter or answer conversion.
    return frames.reshape(-1, 12)

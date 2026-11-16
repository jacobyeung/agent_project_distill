import hashlib
from .vendor import nav_text as NT

def history_indices(t, length=32):
    if t < 0 or length < 1:
        raise ValueError('Invalid history')
    return [t] if length == 1 else [i*t//(length-1) for i in range(length)]

def prompt(instruction, executed=(), output_format='nav', history_frames=32):
    forms = {
        'nav': 'Write one to three actions separated by comma and space: forward 0.25|0.50|0.75, turn_left|turn_right 15|30|45, or stop (only last).',
        'click': f'Write exactly <goal frame={history_frames} x=0.00 y=0.00> with coordinates in [0,1] to two decimals, turn_left 90, turn_right 90, turn_around, or stop.',
        'text': 'Write forward, turn_left, turn_right, stop; or A, B, C, D respectively.',
        'waypoint': 'Write JSON {"heading_deg": number, "distance_m": number, "stop": boolean}. Positive heading turns left.',
        'chunk': 'Write JSON [K,3]: [forward_metres, left_degrees, stop_probability].'}
    return (f'Navigate using {history_frames} frames; frame 1 is the start and frame {history_frames} is current.\n'
            f'Instruction: {instruction}\nExecuted: {", ".join(executed)}\n{forms[output_format]}')

TEMPLATE_ID = 'navrun_native_thinking_v1'
TEMPLATE_SHA256 = hashlib.sha256('\n'.join(prompt('{instruction}', ['{executed}'], f) for f in
                                        ('nav', 'click', 'text', 'waypoint', 'chunk')).encode()).hexdigest()

def messages(instruction, executed=(), output_format='nav', history_frames=32):
    """Call the model's native thinking chat template; never add an MC answer suffix."""
    return [{'role': 'user', 'content': prompt(instruction, executed, output_format, history_frames)}]

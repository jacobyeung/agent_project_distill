import json
from functools import wraps

class UnmappedGroundingLabel(RuntimeError):
    def __init__(self, label, labels):
        self.refusal = {
            'status': 'refused', 'error': 'unmapped_grounding_label',
            'rule': 'sealed_REQ07_REQ16_label_match', 'requested_label': label,
            'available_scene_labels': sorted(labels),
            'action': 'Retry with a label from available_scene_labels; the sealed matcher does not map this label.',
        }
        super().__init__(json.dumps(self.refusal, sort_keys=True))


def grounding_refusal(function):
    """Keep a typed label refusal in the normal planner tool-result channel."""
    @wraps(function)
    def wrapped(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except UnmappedGroundingLabel as error:
            return error.refusal
    return wrapped


"""Open-vocabulary name audit, recognized qualifiers and instance admission."""
import numpy as np
import unicodedata
from scipy import ndimage

# Literal training vocabulary; multiword labels such as office chair are atomic.
LABELS = ('armchair', 'backpack', 'bag', 'ball', 'bar', 'basket', 'bathroom cabinet', 'bathroom stall', 'bathroom stall door', 'bathroom vanity', 'bathtub', 'bed', 'bench', 'blackboard', 'blanket', 'board', 'book', 'books', 'bookshelf', 'bottle', 'box', 'bucket', 'bulletin board', 'cabinet', 'cabinets', 'chair', 'clock', 'closet', 'closet doors', 'clothes', 'clothing', 'coffee maker', 'coffee table', 'computer tower', 'copier', 'couch', 'counter', 'cup', 'curtain', 'decoration', 'desk', 'dish rack', 'dishwasher', 'door', 'doorframe', 'doors', 'dresser', 'dumbbell', 'end table', 'fan', 'file cabinet', 'fire extinguisher', 'guitar', 'jacket', 'keyboard', 'kitchen cabinet', 'kitchen cabinets', 'kitchen counter', 'lamp', 'laptop', 'laundry basket', 'laundry hamper', 'ledge', 'light', 'light switch', 'mat', 'microwave', 'mini fridge', 'mirror', 'monitor', 'mouse', 'nightstand', 'office chair', 'ottoman', 'paper', 'paper bag', 'paper cutter', 'paper towel dispenser', 'paper towel roll', 'person', 'piano', 'picture', 'pillow', 'plant', 'plunger', 'printer', 'purse', 'radiator', 'range hood', 'recycling bin', 'refrigerator', 'shelf', 'shoes', 'shower', 'shower curtain', 'shower curtain rod', 'shower walls', 'sink', 'soap dish', 'soap dispenser', 'sofa chair', 'stair rail', 'stairs', 'stool', 'storage bin', 'stove', 'suitcase', 'table', 'telephone', 'tissue box', 'toilet', 'toilet paper', 'towel', 'trash bin', 'trash can', 'tray', 'tube', 'tv', 'tv stand', 'wardrobe closet', 'water cooler', 'whiteboard', 'window', 'windowsill')


def normalized_name(name):
    from trace_format.contracts import new_contracts
    if new_contracts():
        from .phrases import normalize_phrase
        return normalize_phrase(name)
    return ' '.join(unicodedata.normalize('NFKC', name).casefold().split())


def outside_vocabulary(name, labels=LABELS):
    """Audit only: vocabulary membership must never refuse an unknown noun."""
    return normalized_name(name) not in {normalized_name(label) for label in labels}


def qualification(name, labels=LABELS):
    normalized = normalized_name(name)
    literals = {normalized_name(label) for label in labels}
    if normalized in literals:
        return False
    modifiers = set('the a an red blue green white black brown yellow orange purple pink gray grey wooden metal plastic small large big little left right leftmost rightmost nearest closest first second third two three four'.split())
    relations = ('on ', 'to the ', 'near ', 'behind ', 'under ', 'beside ', 'between ', 'next to ')
    for label in literals:
        for literal in (label, label+'s'):
            if normalized.endswith(' '+literal):
                prefix = normalized[:-len(literal)].strip().split()
                if prefix and all(word in modifiers for word in prefix):
                    return True
            if normalized.startswith(literal+' ') and normalized[len(literal)+1:].startswith(relations):
                return True
    # Unrecognized complete names remain valid open-vocabulary queries.
    return False


def component_counts(masks, prob, tau):
    """Audit 8-connected mask pieces; occlusion makes instance counts unknown."""
    raw, substantial = [], []
    for mask, p in zip(masks, prob):
        if p < tau:
            raw.append(0); substantial.append(0)
            continue
        components, count = ndimage.label(mask, structure=np.ones((3, 3)))
        sizes = np.bincount(components.ravel())[1:]
        raw.append(int(count))
        substantial.append(int((sizes >= max(16, .10 * np.count_nonzero(mask))).sum()))
    return raw, substantial


def multiple_instances(masks, prob, tau):
    """Legacy component-proxy API; this is never a response refusal."""
    return any(count > 1 for count in component_counts(masks, prob, tau)[1])


def admitted_result(name, masks, prob, geometry, tau, *, qualified=False):
    from .ground_lifting import lift_object
    raw, substantial = component_counts(masks, prob, tau)
    flags = dict(qualified=qualified, multi_instance=None,
                 mask_component_counts=raw, substantial_component_counts=substantial,
                 has_multiple_mask_components=any(count > 1 for count in raw),
                 refusal_reason='qualified_label' if qualified else None)
    result = dict(name=name, seen=False) if qualified else lift_object(name, masks, prob, geometry, tau=tau)
    return result, flags

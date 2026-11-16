"""Fixed opening prose. Inputs are named roles, requested frames and a distance branch."""

HEADS = ("depth_at unprojects each click with the depth and field-of-view heads and the pose head places it in "
         "frame-1 coordinates (x right, y up, z forward), so points from different frames are directly comparable.")
HEADS_ONE = ("depth_at unprojects each click with the depth and field-of-view heads and prints its camera coordinates "
             "(x right, y up, z forward); the pose head supplies its frame-1 coordinates (x right, y up, z forward).")
SPREAD = "I accept spread up to 0.25, or 0.10 within 40 grid units of the image border."


def count_noun(name):
    if not isinstance(name, str): return name
    name = name.replace("(s)", "").strip()
    prefix, _, word = name.rpartition(" ")
    singular = {"books": "book", "doors": "door", "chairs": "chair", "tables": "table",
                "lamps": "lamp", "cabinets": "cabinet", "shelves": "shelf", "bookshelves": "bookshelf",
                "boxes": "box", "benches": "bench", "couches": "couch", "sofas": "sofa",
                "beds": "bed", "windows": "window", "pictures": "picture", "frames": "frame"}
    unchanged = {"clothes", "clothing", "pants", "trousers", "scissors", "news", "series", "species",
                 "canvas", "gas", "status"}
    if word in singular: word = singular[word]
    elif word not in unchanged:
        if word.endswith('ies') and len(word) > 3: word = word[:-3]+'y'
        elif word.endswith(('ches', 'shes', 'xes', 'zes')): word = word[:-2]
        elif word.endswith('s') and not word.endswith(('ss', 'us', 'is')): word = word[:-1]
    name = (prefix+" " if prefix else "") + word
    return name


def noun(name):
    """Preserve source-bound object names in every non-count sentence."""
    return name


def plural(name, n):
    name = count_noun(name)
    if n == 1: return name
    prefix, _, word = name.rpartition(" ")
    irregular = {"person": "people", "child": "children", "man": "men", "woman": "women",
                 "mouse": "mice", "goose": "geese", "foot": "feet", "tooth": "teeth",
                 "shelf": "shelves", "bookshelf": "bookshelves", "knife": "knives",
                 "leaf": "leaves", "life": "lives", "wife": "wives", "wolf": "wolves",
                 "loaf": "loaves", "calf": "calves", "half": "halves", "scarf": "scarves",
                 "bus": "buses", "gas": "gases", "canvas": "canvases", "status": "statuses"}
    unchanged = {"clothing", "furniture", "equipment", "luggage", "deer", "sheep", "fish",
                 "series", "species", "clothes", "pants", "trousers", "scissors", "glasses"}
    if word in irregular: result = irregular[word]
    elif word in unchanged: result = word
    elif word.endswith(("ss", "ch", "sh", "x", "z")): result = word+"es"
    elif word.endswith("s"): result = word
    elif len(word) > 1 and word.endswith("y") and word[-2] not in "aeiou": result = word[:-1]+"ies"
    else: result = word+"s"
    return (prefix+" " if prefix else "")+result


def phrases(config, qid):
    from .common import pinned, read_json, digest, Refusal
    bank = {"multi_frame": [HEADS], "single_frame": [HEADS_ONE], "spread_rule": [SPREAD]}
    if config.get("phrase_bank"):
        bank = read_json(pinned(config["phrase_bank"]))
        if any(not isinstance(bank.get(k), list) or not bank[k] or
               any(not isinstance(x, str) or not x.strip() or "<" in x or "\n" in x for x in bank[k]) for k in
               ("multi_frame", "single_frame", "spread_rule")):
            raise Refusal("phrase_bank_schema")
    return {k: bank[k][int(digest([qid, k]), 16) % len(bank[k])] for k in bank}


def frame_look(objects, frames):
    if len(set(frames)) == 1:
        return f"Frame {frames[0]} shows {'both ' if len(objects) == 2 else ''}" + join("the "+noun(o) for o in objects) + ", so one view is enough."
    return "The objects appear in different views; I will compare candidate views before combining the points."


def enrich_opening(text, family, choices, config, qid, has_depth):
    if family in ('object_counting', 'absolute_count', 'relative_count'):
        return text
    bank = phrases(config, qid)
    text = text.replace(HEADS, bank['multi_frame']).replace(HEADS_ONE, bank['single_frame'])
    if any(c.get('single_view_limit') for c in choices):
        text += " I use one view per object for this comparison."
    if any(c.get('kind') in ('pair','reference_pair') or c.get('rankings') for c in choices):
        text += " I choose separate views by the smallest frame separation among usable pairs, breaking ties by the first frame, then the second."
    if has_depth: text += " " + bank['spread_rule']
    return text


from functools import lru_cache


@lru_cache(maxsize=1)
def _qwen_counter():
    from pathlib import Path
    from .common import source_module, Refusal
    paths = [Path(__file__).resolve().parents[1]/'ops/qwen_token_counter.py',
             Path('/scratch/jjyeung/orch_cd/derivgen/ops/qwen_token_counter.py')]
    path = next((p for p in paths if p.is_file()),None)
    if path is None: raise Refusal('missing_pinned_qwen_counter')
    return source_module('derivgen_qwen_counter', {
        'path': str(path),
        'sha256': '2654ff6414c5c03abc97f8ea5ece96bcf42abc81126350fab5368c97e4c787ec'})


def qwen_tokens(text):
    """Use the parent-pinned local counter for the multi-view length decision."""
    return _qwen_counter().count_tokens(text)


def view_selection_target(record):
    """Preserve the frame/click budget with the expanded closest response length.

    This string is private length evidence, never emitted as a training target.
    """
    from .canon_render import render
    events = []
    for event in record['events']:
        if event['kind'] == 'calculator_response' and event['response']['op'] == 'closest':
            response = event['response']
            pairs = '\n'.join(f"{p['a']}-{p['b']} {p['value']:.2f} m" for p in response['result']['pairs'])
            text = pairs + '\n' + response['text']
            event = {**event, 'response': {**response, 'text': text,
                     'injected_text': '<tool_response>' + text + '</tool_response>'}}
        events.append(event)
    return render(events, record['answer'])['target']


def join(items):
    items = list(items)
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]


PLAN = {
    "distance": "I will compare candidate views of the {a} and the {b}, click their facing surfaces, and measure the smallest click-pair distance. {heads}",
    "rel_distance": "Okay, I need to find which of {cands} is closest to the {target}, measuring from the closest points. For each candidate I will pick a frame that shows it together with the {target} (or, if none does, a pair of frames showing the two objects), locate both with middle clicks to see which sides face each other, click those facing sides, and take the smallest click-pair distance. Then I compare the candidates. {heads}",
    "size": "Okay, I need the longest side of {objs}. I will pick the frame where the object is most fully visible, click the two ends of its longest visible side (and its top and bottom when the height could be longer), and let the calculator measure the distances. {heads}",
    "counting": "I click every {cat_word} in each frame where one is visible, take the most seen together as a floor, then count over the whole video.",
    "direction": "Okay, standing at the {stand} and facing the {face}, I need the direction of the {query}. I will locate the three objects with middle clicks, then the calculator projects them onto the floor, forms u = facing - standing and v = query - standing, and gives dot, cross and the signed angle. {heads}",
    "route": "Okay, I start at the {start} facing the {face} and follow the route to the {goal}. I will locate every landmark with a middle click; at each blank, the turn is the signed angle between my current heading and the direction to the next waypoint, read from the calculator. {heads}",
    "appearance": "Okay, I need the order in which {cats} first appear. I will look through the 32 frames in order, note the first frame where I can point at each category, and sort the categories by that frame.",
    "camera_move": "Okay, I need to measure how the camera moved between frame {i} and frame {j}. The pose head with the scale head gives the metric camera motion, which the move tool prints in the starting frame's level coordinates.",
    "camera_obj": "Okay, I need the distance from the camera in frame {k} to {objs}. I will click the parts nearest the camera in that frame; the calculator's cam_dist gives each point's distance from its own camera. {heads}",
    "obj_obj": "Okay, I need where the {a} is relative to the {ref} in frame {k}. I will click near the middle of each in that frame and compare their {what}. {heads}",
}


def opening_text(family, roles, *, common_frame=None):
    """Format source-bound names/frames; None denotes a cross-frame distance.

    Callers establish roles and the observable distance branch independently.
    This function only formats text and has no execution or data access.
    """
    t = family
    p = {k: noun(v) if isinstance(v, str) else [noun(x) for x in v] if isinstance(v, list) else v for k, v in roles.items()}
    if t in ("object_counting", "absolute_count", "relative_count"):
        p = {k: count_noun(v) if isinstance(v, str) else v for k, v in p.items()}
    heads = HEADS
    if t == "room_size_estimation":
        return "I will click the reviewed whole-scene floor corners in polygon order, lift them to frame 1 and use area to measure the floor. " + heads
    if t == "camera_rotation":
        return f"I will use the pose head's turn from frame {p['i']} to frame {p['j']}, wrapped to (-180, 180], with positive turn meaning left and a half turn reported as +180 degrees."
    if t in ("object_abs_distance", "absolute_distance_object"):
        frames = "I will inspect the frames to choose views of the two objects."
        return f"I will compare surface points on the {p['a']} and the {p['b']} to find their shortest distance. " + heads
    if t in ("object_rel_distance", "relative_distance_object"):
        return f"I will measure one set of points on the {p['target']}, reuse it to compare the closest distances to {join('the '+x for x in p['cands'])}, and choose the nearest. " + heads
    if t in ("object_size_estimation", "absolute_size_object"):
        return PLAN["size"].format(objs=f"the {p['a']}", heads=heads)
    if t == "relative_size_object":
        return PLAN["size"].format(objs=f"the {p['a']} and of the {p['b']}, then compare them", heads=heads)
    if t in ("object_counting", "absolute_count"):
        return PLAN["counting"].format(cats=f"the {plural(p['cat'], 2)}", cat_word=p["cat"], heads=heads)
    if t == "relative_count":
        return f"I click every {p['a']} and every {p['b']} in each frame where one is visible, take the most seen together in each category as a floor, then count both over the whole video and compare the counts."
    if t.startswith("object_rel_direction") or t in ("relative_direction_object", "absolute_direction_object"):
        return f"I will locate the {p['stand']}, {p['face']} and {p['query']} with middle clicks to find the direction of the {p['query']} when standing at the {p['stand']} facing the {p['face']}. " + heads
    if t == "route_planning":
        return PLAN["route"].format(start=p["start"], face=p["face"], goal=p["goal"], heads=heads)
    if t == "obj_appearance_order":
        return PLAN["appearance"].format(cats=join(p["cats"]))
    if t in ("camera_displacement", "camera_movement_direction"):
        return PLAN["camera_move"].format(i=p["i"], j=p["j"])
    if t == "camera_obj_abs_dist" or t.startswith("camera_obj_rel_dist"):
        objs = f"the nearest point of the {p['obj']}" if "obj" in p else "each of " + join(f"the {x}" for x in p["cands"]) + ", and pick the closest"
        return f"I will compare near-surface clicks on {objs} with the camera in frame {p['k']}. " + HEADS_ONE if t.startswith("camera_obj_rel_dist") else f"I will measure the nearest surface point of the {p['obj']} from the camera in frame {p['k']}. " + HEADS_ONE
    what = {"lr": f"horizontal positions: in frame {p['k']}'s view, larger x is further right", "nf": "middles' distances from the camera", "ud": "frame-1 heights from the pose head (y up)"}[t[-2:]]
    return PLAN["obj_obj"].format(a=p["a"], ref=p["ref"], k=p["k"], what=what, heads=HEADS_ONE)

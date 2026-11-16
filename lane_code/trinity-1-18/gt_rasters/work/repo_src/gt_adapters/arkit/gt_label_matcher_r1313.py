"""Answer-free label matcher extracted from the sealed REQ-07/REQ-16 source."""

_LABEL_SYNONYMS: dict[str, list[str]] = {
    "trash bin": ["trash can", "garbage can", "garbage bin", "rubbish bin", "waste basket", "wastebasket", "recycling bin"],
    "trash can": ["trash bin", "garbage can", "garbage bin", "rubbish bin"],
    "garbage bin": ["trash can", "trash bin"], "rubbish bin": ["trash can", "trash bin"],
    "bin": ["trash can", "trash bin", "garbage can", "recycling bin"],
    "sofa": ["couch", "armchair", "loveseat"], "couch": ["sofa"],
    "armchair": ["chair", "couch", "sofa"],
    "chair": ["office chair", "armchair", "folded chair", "dining chair", "stool"],
    "table": ["desk", "coffee table", "dining table", "end table", "kitchen table", "nightstand", "side table"],
    "desk": ["table", "office desk", "computer desk"], "coffee table": ["table"],
    "cabinet": ["kitchen cabinet", "file cabinet", "storage cabinet", "cupboard", "cabinets"],
    "cupboard": ["cabinet", "kitchen cabinet"],
    "shelf": ["bookshelf", "shelving", "shelves", "bookshelves", "book shelf"],
    "bookshelf": ["shelf", "shelves"], "wardrobe": ["closet", "cabinet"],
    "closet": ["wardrobe", "cabinet"], "fridge": ["refrigerator", "mini fridge"],
    "refrigerator": ["fridge", "mini fridge"], "mini fridge": ["fridge", "refrigerator"],
    "tv": ["television", "monitor", "tv stand"], "television": ["tv", "monitor"],
    "monitor": ["computer monitor", "screen", "display"],
    "washing machine": ["washer", "dryer"], "microwave": ["microwave oven"],
    "lamp": ["table lamp", "floor lamp", "desk lamp", "ceiling light", "light", "lighting", "lantern"],
    "light": ["lamp", "ceiling light", "ceiling lamp"], "ceiling light": ["lamp", "light"],
    "picture": ["painting", "poster", "photo", "wall picture", "framed picture", "photograph", "artwork"],
    "painting": ["picture", "artwork"], "plant": ["potted plant", "flower", "flowers", "vase"],
    "vase": ["flower vase", "plant vase"], "mirror": ["wall mirror", "bathroom mirror"],
    "door": ["doorframe", "doors"], "doorframe": ["door"],
    "window": ["windowframe", "window frame"], "bed": ["mattress", "bunk bed"],
    "mattress": ["bed"], "pillow": ["cushion"], "stove": ["oven", "cooktop", "range"],
    "oven": ["stove"], "counter": ["countertop", "kitchen counter", "breakfast bar"],
    "sink": ["bathroom sink", "kitchen sink"], "toilet": ["toilet seat"],
    "towel": ["bath towel", "hand towel"], "bathtub": ["bath tub", "tub"],
    "keyboard": ["computer keyboard"], "mouse": ["computer mouse"],
    "computer mouse": ["mouse"], "laptop": ["computer", "notebook"],
    "computer": ["laptop", "desktop", "pc"], "backpack": ["bag", "bookbag"],
    "bag": ["backpack", "purse", "handbag"], "box": ["cardboard box", "storage box"],
    "blanket": ["comforter", "quilt"], "curtain": ["curtains", "drape", "drapes"],
    "rug": ["carpet", "mat"], "carpet": ["rug"],
}


def match_label(query: str, label_to_ids: dict[str, list[int]]) -> list[int]:
    q = query.lower().strip()
    if not q:
        return []
    if q in label_to_ids:
        return list(label_to_ids[q])
    matches = [obj_id for label, ids in label_to_ids.items()
               if q in label or label in q for obj_id in ids]
    if matches:
        return matches
    for synonym in _LABEL_SYNONYMS.get(q, []):
        matches = [obj_id for label, ids in label_to_ids.items()
                   if synonym == label or synonym in label or label in synonym
                   for obj_id in ids]
        if matches:
            return matches
    stopwords = {"the", "a", "an", "of", "and"}
    query_tokens = {token for token in q.split()
                    if len(token) >= 3 and token not in stopwords}
    if not query_tokens:
        return []
    matches = []
    for label, ids in label_to_ids.items():
        label_tokens = {token for token in label.split()
                        if len(token) >= 3 and token not in stopwords}
        if query_tokens & label_tokens:
            matches.extend(ids)
    return matches


__all__ = ["match_label"]

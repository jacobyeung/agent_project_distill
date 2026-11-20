

SINGULAR = {'kitchen cabinets': 'kitchen cabinet', 'cabinets': 'cabinet', 'chairs': 'chair',
            'tables': 'table', 'doors': 'door', 'windows': 'window', 'shelves': 'shelf',
            'bookshelves': 'bookshelf', 'desks': 'desk', 'beds': 'bed', 'sofas': 'sofa',
            'couches': 'couch', 'curtains': 'curtain', 'blinds': 'window blind',
            'books': 'book', 'pillows': 'pillow', 'lamps': 'lamp', 'boxes': 'box',
            'pictures': 'picture', 'towels': 'towel', 'clothes': 'clothing',
            'clothes dryers': 'clothes dryer', 'pipes': 'pipe'}

def normalize_phrase(label: str) -> str:
    label = ' '.join(label.lower().replace('_', ' ').split())
    return SINGULAR.get(label, label)

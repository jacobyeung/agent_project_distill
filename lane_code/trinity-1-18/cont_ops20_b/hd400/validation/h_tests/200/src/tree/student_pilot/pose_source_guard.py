"""Reject the A4 r_s stream that overlaps the clean camera evaluation pool."""
import re


_NAME = re.compile(r'(?<![A-Za-z0-9_])r_s(?![A-Za-z0-9_])')
# The scene-audit/Orchard receipt names this source by its retained pin prefix.
_RECEIPT = '521fcc55'


def refuse_a4_r_s(value):
    if isinstance(value, dict):
        if str(value.get('sha256', '')).startswith(_RECEIPT):
            raise ValueError('A4 r_s overlaps the clean camera pool and cannot enter a pose stream')
        for key, item in value.items():
            if _NAME.search(str(key)):
                raise ValueError('A4 r_s overlaps the clean camera pool and cannot enter a pose stream')
            refuse_a4_r_s(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            refuse_a4_r_s(item)
    elif isinstance(value, str) and _NAME.search(value):
        raise ValueError('A4 r_s overlaps the clean camera pool and cannot enter a pose stream')

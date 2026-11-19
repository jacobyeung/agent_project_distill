"""Hash encoded tensor values, including scalar shape/dtype and container structure."""
import hashlib
import json
import torch


def encoded_hash(value):
    digest = hashlib.sha256()
    def visit(item):
        if isinstance(item, torch.Tensor):
            tensor = item.detach().cpu().contiguous()
            digest.update(json.dumps([str(tensor.dtype), list(tensor.shape)]).encode())
            digest.update(tensor.reshape(-1).view(torch.uint8).numpy().tobytes())
        elif isinstance(item, dict):
            digest.update(b'dict')
            for key in sorted(item):
                digest.update(json.dumps(key).encode())
                visit(item[key])
        elif isinstance(item, (list, tuple)):
            digest.update(str((type(item).__name__, len(item))).encode())
            for child in item:
                visit(child)
        else:
            digest.update(json.dumps(item, sort_keys=True).encode())
    visit(value)
    return digest.hexdigest()


def compare_rows(reference, trial):
    if any('row_draws' in record for record in reference + trial):
        if [record.get('row_draws') for record in reference] != [record.get('row_draws') for record in trial]:
            raise ValueError('Row draws differ from OFF')
    expected = [record['encoded_row_sha256'] for record in reference]
    actual = [record['encoded_row_sha256'] for record in trial]
    if not expected or expected != actual:
        raise ValueError('Encoded row SHA-256 differs from OFF')

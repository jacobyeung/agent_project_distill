from common import sha


ARCHIVE_SHA = 'b3fa05c6d5fc51e56b41c106ba58209cb220e72d511c284ece4c109ce3c56509'
CODE = {
    'variant_cache.py': 'cb702acdd4e88a47f1ce7d8556ecce0c54936382422e94c031b9d83b5e02a284',
    'cache_masks.py': 'e1a2730e4566b555a9129fcdce06ff1290d9916fc2d0f9a59cadbf8f1fb0629c',
    'kitlib.py': 'c377025b67e7bf83da516e110d79566ce937c6806500f62796a937d0da92a244',
    'variantlib.py': '10219e028f26caa5d6cf76e42e6739f8ebd68204faf135874974e593d5440198',
    'vendor/sam_backend.py': '356802c9c86c79975a479fab84227ab14fedd67910239760cb4456e8c9c15d3c',
    'vendor/sam3_tower.py': '617d5c8daa31ee2de62efe5c93ed32f50203805006dce5bb75d9959a16e4decb',
    'vendor/phrase.py': 'e0f429bfb8fbd013570fea3ede806d051516ad7c6e380561f5061168b756863c',
    'vendor/stub_backend.py': 'a311ac4fc353a3948c05db4b6054c8a2652c3e7c9f0b4f4859b80ad3807678b4',
}


def identity():
    return dict(archive_sha256=ARCHIVE_SHA, inference_code_sha256=dict(CODE),
                image_batch_size=1, native_image_batch=False)


def verify_local(root):
    if sha(root/'kit_combo3.tar.gz') != ARCHIVE_SHA:
        raise ValueError('Frozen kit_combo3 archive hash differs')
    for name in ('kitlib.py', 'variantlib.py', 'vendor/phrase.py'):
        if sha(root/name) != CODE[name]:
            raise ValueError('Frozen kit_combo3 validator differs: '+name)


def validate_code(manifest, binding):
    code = manifest.get('experiment', {}).get('inference_code_sha256')
    dense = manifest.get('experiment', {}).get('dense_source', {})
    if code != CODE or binding.get('code_sha256') != CODE or dense.get('code_sha256') != CODE:
        raise ValueError('SAM3 inference code differs from frozen kit_combo3')
    for settings in (manifest, manifest['experiment'], binding):
        if (type(settings.get('image_batch_size', 1)) is not int or settings.get('image_batch_size', 1) != 1
                or settings.get('native_image_batch', False) is not False):
            raise ValueError('Frozen SAM3 requires image batch size 1 without native batching')

# trust-but-verify corpus specimen. Label + rationale: test-corpus/manifest.yaml
import hashlib
def cache_key(data):
    return hashlib.md5(data).hexdigest()

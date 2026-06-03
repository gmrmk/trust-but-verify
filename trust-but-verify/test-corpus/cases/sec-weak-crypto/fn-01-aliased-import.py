# trust-but-verify corpus specimen. Label + rationale: test-corpus/manifest.yaml
from hashlib import md5 as _h
def store_password(pw):
    return _h(pw.encode()).hexdigest()

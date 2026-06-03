# trust-but-verify corpus specimen. Label + rationale: test-corpus/manifest.yaml
import hashlib
def store_password(pw):
    return hashlib.md5(pw.encode()).hexdigest()

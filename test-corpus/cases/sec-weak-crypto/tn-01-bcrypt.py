# trust-but-verify corpus specimen. Label + rationale: test-corpus/manifest.yaml
import bcrypt
def store_password(pw):
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt())

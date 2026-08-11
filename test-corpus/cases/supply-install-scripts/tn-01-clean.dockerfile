# trust-but-verify corpus specimen. Label + rationale: test-corpus/manifest.yaml
FROM debian:12
RUN apt-get update && apt-get install -y --no-install-recommends git

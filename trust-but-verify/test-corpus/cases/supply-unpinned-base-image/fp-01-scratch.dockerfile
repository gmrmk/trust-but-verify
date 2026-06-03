# trust-but-verify corpus specimen. Label + rationale: test-corpus/manifest.yaml
FROM scratch
COPY --from=builder /app/bin /bin
ENTRYPOINT ["/bin/app"]

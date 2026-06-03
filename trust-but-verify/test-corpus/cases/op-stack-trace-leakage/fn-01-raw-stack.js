// trust-but-verify corpus specimen. Label + rationale: test-corpus/manifest.yaml
app.get("/x", (req, res) => {
  try { doWork(); }
  catch (e) { res.status(500).send(e.stack); }
});

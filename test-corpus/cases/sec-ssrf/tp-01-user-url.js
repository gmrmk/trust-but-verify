// trust-but-verify corpus specimen. Label + rationale: test-corpus/manifest.yaml
async function proxy(req, res) {
  const r = await fetch(req.query.target);
  res.send(await r.text());
}
module.exports = { proxy };

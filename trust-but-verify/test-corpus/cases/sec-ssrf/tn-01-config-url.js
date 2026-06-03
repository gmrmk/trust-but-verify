// trust-but-verify corpus specimen. Label + rationale: test-corpus/manifest.yaml
async function health(req, res) {
  const r = await fetch(config.upstreamUrl);
  res.json({ ok: r.ok });
}
module.exports = { health };

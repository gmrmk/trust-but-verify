// trust-but-verify corpus specimen. Label + rationale: test-corpus/manifest.yaml
async function getUser(req, res) {
  const r = await fetch(`https://api.example.com/users/${req.params.id}`);
  res.json(await r.json());
}
module.exports = { getUser };

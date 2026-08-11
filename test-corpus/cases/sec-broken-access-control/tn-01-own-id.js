// trust-but-verify corpus specimen. Label + rationale: test-corpus/manifest.yaml
async function me(req, res) {
  const user = await User.findById(req.user.id);
  res.json(user);
}
module.exports = { me };

// trust-but-verify corpus specimen. Label + rationale: test-corpus/manifest.yaml
const got = require("got");
async function proxy(req, res) {
  const r = await got(req.query.target);
  res.send(r.body);
}
module.exports = { proxy };

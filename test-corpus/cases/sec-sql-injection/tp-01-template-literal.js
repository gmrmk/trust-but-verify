// trust-but-verify corpus specimen. Label + rationale: test-corpus/manifest.yaml
const db = require("./db");
function search(req, res) {
  const term = req.query.term;
  return db.query(`SELECT id, email FROM users WHERE name LIKE '%${term}%'`);
}
module.exports = { search };

// trust-but-verify corpus specimen. Label + rationale: test-corpus/manifest.yaml
const db = require("./db");
function search(req, res) {
  const term = req.query.term;
  const sql = "SELECT id, email FROM users WHERE name LIKE ?";
  return db.query(sql, [`%${term}%`]);
}
module.exports = { search };

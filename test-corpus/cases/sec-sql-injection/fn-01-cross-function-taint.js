// trust-but-verify corpus specimen. Label + rationale: test-corpus/manifest.yaml
const db = require("./db");
function collectFilters(req) {
  return { where: `status = '${req.query.status}'`, limit: 50 };
}
function buildAndRun(filter) {
  return db.query(`SELECT * FROM orders WHERE ${filter.where} LIMIT ${filter.limit}`);
}
async function handler(req, res) {
  const filter = collectFilters(req);
  res.json(await buildAndRun(filter));
}
module.exports = { handler };

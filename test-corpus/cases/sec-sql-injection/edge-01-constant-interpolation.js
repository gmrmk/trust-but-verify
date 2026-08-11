// trust-but-verify corpus specimen. Label + rationale: test-corpus/manifest.yaml
const db = require("./db");
const STATUS_ACTIVE = "active";
function listActive() {
  return db.query(`SELECT id FROM users WHERE status = '${STATUS_ACTIVE}'`);
}
module.exports = { listActive };

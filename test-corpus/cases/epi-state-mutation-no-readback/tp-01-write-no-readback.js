// trust-but-verify corpus specimen. Label + rationale: test-corpus/manifest.yaml
const fs = require("fs");
function persist(out, body) {
  fs.writeFileSync(out, body)
}
module.exports = { persist };

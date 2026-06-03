// trust-but-verify corpus specimen. Label + rationale: test-corpus/manifest.yaml
async function activeUsers(db) {
  return db.find({ active: true });
}
module.exports = { activeUsers };

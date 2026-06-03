// trust-but-verify corpus specimen. Label + rationale: test-corpus/manifest.yaml
async function setStatus(db, id, status) {
  await db.update({ id }, { status });
  const fresh = await db.findOne({ id });
  return fresh.status === status;
}
module.exports = { setStatus };

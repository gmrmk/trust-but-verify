// trust-but-verify corpus specimen. Label + rationale: test-corpus/manifest.yaml
async function archive(db, doc) {
  doc.archived = true;
  await db.save(doc);
}
module.exports = { archive };

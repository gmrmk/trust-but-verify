// trust-but-verify corpus specimen. Label + rationale: test-corpus/manifest.yaml
async function getDoc(req, res) {
  const doc = await db.collection("docs").findOne({ _id: req.params.id });
  res.json(doc);
}
module.exports = { getDoc };

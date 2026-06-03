// trust-but-verify corpus specimen. Label + rationale: test-corpus/manifest.yaml
async function getInvoice(req, res) {
  const inv = await Invoice.findById(req.params.id);
  res.json(inv);
}
module.exports = { getInvoice };

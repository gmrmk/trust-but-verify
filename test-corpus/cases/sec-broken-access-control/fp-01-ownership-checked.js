// trust-but-verify corpus specimen. Label + rationale: test-corpus/manifest.yaml
async function getOrder(req, res) {
  const order = await Order.findById(req.params.id);
  if (!order || order.userId !== req.user.id) return res.status(403).end();
  res.json(order);
}
module.exports = { getOrder };

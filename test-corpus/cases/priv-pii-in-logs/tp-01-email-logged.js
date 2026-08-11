// trust-but-verify corpus specimen. Label + rationale: test-corpus/manifest.yaml
function onLogin(user, logger) {
  logger.info("login succeeded for " + user.email);
}
module.exports = { onLogin };

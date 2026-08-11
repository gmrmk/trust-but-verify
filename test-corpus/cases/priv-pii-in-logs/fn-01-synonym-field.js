// trust-but-verify corpus specimen. Label + rationale: test-corpus/manifest.yaml
function onSignup(profile, logger) {
  logger.info("welcome " + profile.mail);
}
module.exports = { onSignup };

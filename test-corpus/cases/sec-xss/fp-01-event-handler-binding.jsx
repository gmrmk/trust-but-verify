// trust-but-verify corpus specimen. Label + rationale: test-corpus/manifest.yaml
import sanitizeHtml from "sanitize-html";
export function render(el, req) {
  el.innerHTML = sanitizeHtml(req.body.bio);
}

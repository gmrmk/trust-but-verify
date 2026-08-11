// trust-but-verify corpus specimen. Label + rationale: test-corpus/manifest.yaml
import React from "react";
import DOMPurify from "dompurify";
export function RichComment({ comment }) {
  const clean = DOMPurify.sanitize(comment.html, { ADD_ATTR: ["onerror", "onload"] });
  return <div dangerouslySetInnerHTML={{ __html: clean }} />;
}

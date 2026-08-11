// trust-but-verify corpus specimen. Label + rationale: test-corpus/manifest.yaml
import React from "react";
export function CommentBody({ comment }) {
  return <div dangerouslySetInnerHTML={{ __html: comment.html }} />;
}

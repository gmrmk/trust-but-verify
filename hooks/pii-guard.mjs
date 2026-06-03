// hooks/pii-guard.mjs
//
// PreToolUse(Write|Edit|MultiEdit|Bash) HARD STOP. Refuses to write a file or run
// a command (including a git commit) whose text contains a personal-reference /
// role-attribution pattern, or any term on hooks/pii-denylist.txt. Personal data
// must never enter a committed or published artifact: not a commit message, not a
// branch name, not a session log, not a skill file.
//
// This hook exists because that once happened, and it is the forcing function that
// prevents a recurrence. The asymmetry is deliberate: a false stop costs a few
// seconds; a missed leak costs a person their privacy. So it blocks aggressively.
//
// Contract: a PreToolUse hook that exits 2 blocks the tool and shows stderr to the
// model (Claude Code hooks docs, exit-code-2 table). Wire it in settings.json under
// hooks.PreToolUse for matchers Write|Edit|MultiEdit|Bash.

import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));

// The personal-reference / role-attribution search - the teeth. It hard-stops a
// possessive pronoun that ties a relation or a role to the user. Bare nouns alone
// (parent, child, bilateral) are not blocked; only the attribution shape is.
const ROLE_ATTRIBUTION =
  /\b(my|his|her|their|your|the user'?s?)\s+(relative|relation|sibling|parent|brother|sister|mother|father|son|daughter|wife|husband|aunt|uncle|cousin|niece|nephew|mom|dad|grandparent|grandmother|grandfather|fiance|fiancee|spouse|partner|boss|coworker|colleague|friend|neighbor|manager|supervisor|director|founder|chief|officer|cfo|ceo|cto|coo|cmo|cio|vp|president)\b/i;

function denylist() {
  try {
    return readFileSync(join(HERE, "pii-denylist.txt"), "utf8")
      .split("\n").map((s) => s.trim()).filter((s) => s && !s.startsWith("#"));
  } catch {
    return [];
  }
}

function scan(text) {
  if (!text) return null;
  if (ROLE_ATTRIBUTION.test(text)) return text.match(ROLE_ATTRIBUTION)[0];
  const lower = text.toLowerCase();
  for (const term of denylist()) {
    if (lower.includes(term.toLowerCase())) return term;
  }
  return null;
}

let raw = "";
process.stdin.on("data", (c) => (raw += c));
process.stdin.on("end", () => {
  let j = {};
  try {
    j = JSON.parse((raw.charCodeAt(0) === 0xfeff ? raw.slice(1) : raw).trim());
  } catch {
    process.exit(0);
  }

  const ti = j.tool_input || {};
  const surfaces = [ti.content, ti.new_string, ti.old_string, ti.command];
  if (Array.isArray(ti.edits)) {
    for (const e of ti.edits) surfaces.push(e.new_string, e.old_string);
  }

  for (const s of surfaces) {
    const hit = scan(String(s ?? ""));
    if (hit) {
      process.stderr.write(
        `PII GUARD - HARD STOP. This write/command ties a person or role to the user ("${hit}"). ` +
          "Personal data must never enter a committed or published artifact. Remove the attribution " +
          "(no names, no relations, no roles) before retrying. This hook will not write it for you.\n"
      );
      process.exit(2); // block the tool call
    }
  }
  process.exit(0);
});

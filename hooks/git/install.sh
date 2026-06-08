#!/bin/sh
# Activate tracked git hooks for this clone. core.hooksPath is local config and
# is NOT cloned, so each fresh clone runs this once. Idempotent. Run from the
# repo root after the .githooks/ dir is in place.
git config core.hooksPath .githooks
echo "core.hooksPath -> $(git config --get core.hooksPath)"

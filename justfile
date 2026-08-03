# List available recipes
default:
    @just --list

# Bump the version, commit and tag it
set-version version:
    #!/usr/bin/env bash
    set -euo pipefail

    sed -i 's/^version = "[^"]*"/version = "{{version}}"/' pyproject.toml

    # uv.lock records this package's own version, so re-lock before committing
    uv sync --quiet

    git add pyproject.toml uv.lock
    git commit -m "Bump version to {{version}}"
    git tag "v{{version}}"

    echo "Version set to {{version}}, tagged v{{version}}."
    echo
    echo "To publish:  git push <remote> && git push <remote> --tags"
    echo "  ('git push --tags' is required — set-version makes a LIGHTWEIGHT tag,"
    echo "   which --follow-tags does not push. Verify with: git ls-remote --tags <remote> v{{version}})"
    echo "  Remotes here: origin, github."

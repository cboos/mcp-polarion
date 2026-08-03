# List available recipes
default:
    @just --list

# Bump the version, commit and tag it
set-version version:
    #!/usr/bin/env bash
    set -euo pipefail

    # This recipe commits. Anything else in flight would be swept into a commit
    # labelled "Bump version to X", so refuse rather than mislabel it.
    [ -z "$(git status --porcelain -- . ':!pyproject.toml' ':!uv.lock')" ] \
      || { echo "working tree not clean — commit or stash first"; exit 1; }

    # Anchored to the FIRST match: sed is line-based and would otherwise rewrite
    # a `version = ` line in any other TOML table. The address regex must cover
    # the whole assignment, since the empty `s//` reuses it -- match only the
    # `version = ` prefix and you get `version = "new""old"`.
    # (GNU sed. BSD/macOS sed needs `-i ''`.)
    sed -i '0,/^version = "[^"]*"/s//version = "{{version}}"/' pyproject.toml

    # uv.lock records this package's own version, so re-lock BEFORE staging it —
    # invert this and you commit a lock still naming the old version, silently.
    # `uv lock`, not `uv sync`: sync rewrites .venv/Scripts/mcp-polarion.exe,
    # which Windows locks while an MCP client has the server running.
    uv lock --quiet

    git add pyproject.toml uv.lock
    git commit -m "Bump version to {{version}}"
    git tag "v{{version}}"

    echo "Version set to {{version}}, tagged v{{version}}."
    echo
    echo "To publish:  git push <remote> && git push <remote> --tags"
    echo "  ('git push --tags' is required — set-version makes a LIGHTWEIGHT tag,"
    echo "   which --follow-tags does not push.)"
    echo "  Two remotes here (origin, github) and --tags pushes to ONE."
    echo "  Verify each:  git ls-remote --tags origin v{{version}}"
    echo "                git ls-remote --tags github v{{version}}"

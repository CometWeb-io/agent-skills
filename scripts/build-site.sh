#!/usr/bin/env bash
# Assemble the GitHub Pages landing page into one directory.
# The page, its fonts and its media live in site/; this copies them out and
# marks the result as a plain static site.
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
out="${1:-$root/_site}"

case "$(cd "$(dirname "$out")" 2>/dev/null && pwd)/$(basename "$out")" in
  "$root" | "$root/site" | "$root/site/"*)
    echo "FAIL: refusing to build into $out" >&2
    exit 1
    ;;
esac

rm -rf "$out"
mkdir -p "$out"
cp -R "$root/site/." "$out/"
cp "$root/LICENSE" "$out/LICENSE.txt"
touch "$out/.nojekyll"
echo "Site assembled in $out"

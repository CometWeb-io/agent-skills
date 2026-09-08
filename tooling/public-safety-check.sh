#!/usr/bin/env bash
# Fail if private data leaks into the public tree.
#
# Usage:
#   ./scripts/public-safety-check.sh              # working tree (this is what CI runs)
#   ./scripts/public-safety-check.sh --history    # + every blob in every commit
#
# Design notes — each one is a defect this gate previously had:
#   * grep, not rg. The old version wrapped checks in `if rg ...`; a runner without
#     ripgrep made every check pass silently.
#   * A grep exit status >= 2 means a BROKEN PATTERN, and is fatal. Swallowing it is
#     how a malformed regex turns into a green gate that checks nothing. This caught
#     the private-key rule, whose pattern starts with '-' and was being parsed as a
#     grep option; hence -e on every pattern.
#   * Rule fields are split on ':::' , not '|'. Splitting on '|' corrupts any regex
#     that contains an alternation — which is most of them.
#   * Content AND filenames, every file type, whole repo. The 2026-08-26 leak was JSON
#     under docs/demo/, which the old name-only *.md scan could not see.
#   * History mode normalises hits to the same shape as tree mode, so allowlists and
#     the self-exclusion behave identically in both.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

SCAN_HISTORY=0
[[ "${1:-}" == "--history" ]] && SCAN_HISTORY=1

command -v grep >/dev/null || { echo "FATAL: grep unavailable — gate cannot run" >&2; exit 2; }
command -v git  >/dev/null || { echo "FATAL: git unavailable — gate cannot run" >&2; exit 2; }

failures=0
SELF="tooling/public-safety-check.sh"
EXCLUDES=(--exclude-dir=.git --exclude-dir=node_modules --exclude-dir=dist
          --exclude-dir=.venv --exclude-dir=__pycache__ --exclude-dir=.mypy_cache)

# label:::regex[:::allowlist-regex]
# The allowlist is matched against a normalised "/path:line:content" hit. Use it for
# paths where a match is deliberate guidance rather than leaked content. Allowlist
# paths, never whole rules — and never a directory that receives real run artifacts.
CONTENT_RULES=(
  "Notion collection UUID:::collection://[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
  "Notion hub/page ID:::app\.notion\.com/p/[0-9a-f]{20,}|notion\.so/[0-9a-f]{32}"
  "Linear workspace URL:::linear\.app/"
  "Linear issue ID:::(^|[^A-Za-z0-9])COM-[0-9]{1,5}([^A-Za-z0-9]|$)"
  "owner absolute path:::/Users/[A-Za-z0-9._-]+/(Github|Documents|Desktop)/"
  "private vault path:::personal/(gtm-cometweb|nauka)/|<COMETWEB_INTERNAL_ROOT>/:::^/(AGENTS|CONTRIBUTING)\.md:|/source-registry\.json:|/docs/PUBLIC_MIRROR\.md:|/docs/TARGET\.md:"
  "CRM/infra hostname:::app-eu1\.hubspot|api\.betterwebhub\.com|hpanel\.hostinger"
  "OpenAI-style key:::sk-(proj|ant|live|test)?-?[A-Za-z0-9_-]{24,}"
  "GitHub token:::gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}"
  "Slack token/webhook:::xox[baprs]-[A-Za-z0-9-]{10,}|hooks\.slack\.com/services/[A-Z0-9]"
  "Google API key:::AIza[0-9A-Za-z_-]{35}"
  "AWS access key:::(AKIA|ASIA)[0-9A-Z]{16}"
  "private key block:::-----BEGIN [A-Z ]*PRIVATE KEY-----"
  "bearer token:::Bearer [A-Za-z0-9._-]{30,}"
  "DB connection string:::(postgres(ql)?|mysql|mongodb(\+srv)?|redis)://[^[:space:]\"']*:[^[:space:]@\"']+@"
)

NAME_RULES=(
  '*promotion-playbook*' '*GTM-COUNCIL*' '*gtm-council-memo*' '*KROKI-PROMOCJA*'
  '*linear-*' '*.local.json' '.env' '.env.*' '*client_secret*' '*credentials.json'
  '*service-account*.json' '*.pem' '*.key' 'id_rsa*' '.DS_Store'
  '*boardroom*' '*pilot-queue*' '*evidence-register*'
)

# Normalise "./path:line:" and "<sha>:path:line:" to a single "/path:line:" shape.
normalise() { sed -E 's#^[0-9a-f]{40}:#/#; s#^\./#/#'; }

scan() {  # scan <label> <pattern> <allowlist-or-empty> <mode>
  local label="$1" pat="$2" allow="$3" mode="$4" raw rc hits
  set +e
  if [[ "$mode" == history ]]; then
    # shellcheck disable=SC2086
    raw=$(git grep -IEn -e "$pat" $REVS 2>/tmp/.gate_err); rc=$?
  else
    raw=$(grep -rEIn -e "$pat" . "${EXCLUDES[@]}" 2>/tmp/.gate_err); rc=$?
  fi
  set -e
  # 0 = matched, 1 = no match. Anything else is a broken pattern or a broken run,
  # and must never be mistaken for "clean".
  if [[ $rc -gt 1 ]]; then
    echo "FATAL: rule '$label' failed to execute (exit $rc) — pattern is broken, gate is not trustworthy" >&2
    sed 's/^/       /' /tmp/.gate_err >&2 || true
    rm -f /tmp/.gate_err; exit 2
  fi
  rm -f /tmp/.gate_err
  hits=$(printf '%s\n' "$raw" | normalise | grep -v "^/$SELF:" || true)
  [[ -n "$allow" ]] && hits=$(printf '%s\n' "$hits" | grep -Ev "$allow" || true)
  hits=$(printf '%s\n' "$hits" | sed '/^$/d')
  if [[ -n "$hits" ]]; then
    echo "FAIL${mode:+($mode)}: $label:" >&2
    printf '%s\n' "$hits" | head -15 >&2
    failures=1
  fi
}

run_rules() {  # run_rules <mode>
  local rule label pat allow
  for rule in "${CONTENT_RULES[@]}"; do
    label="${rule%%:::*}"; rule="${rule#*:::}"
    if [[ "$rule" == *':::'* ]]; then pat="${rule%%:::*}"; allow="${rule#*:::}"
    else pat="$rule"; allow=""; fi
    scan "$label" "$pat" "$allow" "$1"
  done
}

check_names() {  # check_names <mode> < list-of-paths
  local f base pat
  while IFS= read -r f; do
    [[ -z "$f" ]] && continue
    base=$(basename "$f")
    for pat in "${NAME_RULES[@]}"; do
      # shellcheck disable=SC2053
      if [[ "$base" == $pat ]]; then
        echo "FAIL${1:+($1)}: forbidden filename: $f — private material belongs outside this repo" >&2
        failures=1
      fi
    done
  done
}

echo "==> content scan (working tree)"
run_rules tree
echo "==> filename scan (working tree)"
git ls-files | check_names ""

if [[ -f skills/ai-council/references/notion-bindings.local.json ]]; then
  echo "FAIL: notion-bindings.local.json must not be present in the release tree" >&2
  failures=1
fi

if [[ "$SCAN_HISTORY" -eq 1 ]]; then
  echo "==> history scan ($(git rev-list --all --count) commits)"
  REVS=$(git rev-list --all)
  if [[ -n "$REVS" ]]; then
    run_rules history
    git log --all --diff-filter=A --name-only --format= | sort -u | check_names history
  fi
fi

if [[ "$failures" -ne 0 ]]; then
  echo "" >&2
  echo "Public-safety check FAILED. Do not push. See AGENTS.md 'public repo' rules." >&2
  exit 1
fi
echo "OK: public-safety check passed$([[ "$SCAN_HISTORY" -eq 1 ]] && echo ' (incl. history)')"

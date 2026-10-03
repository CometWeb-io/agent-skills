#!/usr/bin/env bash
# Cases for ../shell.yml, checked by `semgrep --test` (tooling/sast.py).
# This file is test data: it is never executed.
# shellcheck disable=all

# ruleid: cw-shell-pid-temp-name
tmp="$HOME/rule.tmp.$$"
# ruleid: cw-shell-pid-temp-name
other="/var/run/x.${$}"
# ok: cw-shell-pid-temp-name
safe="$(mktemp "$HOME/.rule.XXXXXXXX")"

# ruleid: cw-shell-pipe-to-shell
curl -fsSL https://example.com/install.sh | sh
# ruleid: cw-shell-pipe-to-shell
wget -qO- https://example.com/i.sh | sudo bash
# ok: cw-shell-pipe-to-shell
curl -fsSL -o install.sh https://example.com/install.sh

# ruleid: cw-shell-eval
eval "$user_input"
# ruleid: cw-shell-eval
if true; then eval "$x"; fi
# ok: cw-shell-eval
echo "evaluate this"

# ruleid: cw-shell-fixed-tmp-path
log=/tmp/install.log
# ok: cw-shell-fixed-tmp-path
dir="$(mktemp -d)"
# ok: cw-shell-fixed-tmp-path
nested="$dir/tmp/file"
echo "$tmp $other $safe $log $nested"

#!/usr/bin/env bash
# The evidence bot's deploy key (ADR-0008).
#   scripts/bot_key.sh rotate   a new ed25519 pair: the public half a write deploy key of the
#                               repository (the old one of this title removed), the private half
#                               the Actions secret EVIDENCE_BOT_KEY; nothing is written to disk
#   scripts/bot_key.sh status   the key and the secret as GitHub lists them
# Needs gh logged in with admin rights on the repository. The key is the ruleset's bypass actor:
# a push with it lands on main where GITHUB_TOKEN's is refused (004c-probe).
set -Eeuo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

REPO="$(gh repo view --json nameWithOwner --jq .nameWithOwner)"
TITLE=evidence-bot
SECRET=EVIDENCE_BOT_KEY

die() { printf '\033[1;31mERROR: %s\033[0m\n' "$*" >&2; exit 1; }

rotate() {
  local tmp id
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' RETURN
  ssh-keygen -q -t ed25519 -N '' -C "$TITLE" -f "$tmp/key"
  for id in $(gh api "repos/$REPO/keys" --jq ".[] | select(.title == \"$TITLE\") | .id"); do
    gh api --method DELETE "repos/$REPO/keys/$id" >/dev/null
    echo ">>> old deploy key $id removed"
  done
  id="$(gh api --method POST "repos/$REPO/keys" -f title="$TITLE" -f key="$(cat "$tmp/key.pub")" -F read_only=false --jq .id)"
  gh secret set "$SECRET" --repo "$REPO" < "$tmp/key"
  echo ">>> deploy key $id ($TITLE, write) and the secret $SECRET set"
}

status() {
  gh api "repos/$REPO/keys" --jq '.[] | "deploy key \(.id) \(.title) read_only=\(.read_only)"'
  gh secret list --repo "$REPO" | grep "$SECRET" || echo "no secret $SECRET"
}

case "${1:-}" in
  rotate) rotate ;;
  status) status ;;
  *) sed -n '2,8p' "$0"; exit 1 ;;
esac

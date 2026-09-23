# Signed commits

Release integrity for this repository assumes authenticated authorship on `main`.

## Current ruleset posture

The **Protect main** ruleset requires a PR and the `validate` status check. It
does **not** yet require signed commits, because GitHub account signing keys
must be registered first. Enabling the rule without keys would block merges.

## One-time setup (SSH signing — preferred)

```bash
# 1. Ensure an SSH key exists
ls ~/.ssh/*.pub

# 2. Register it with GitHub as a *signing* key (Settings → SSH and GPG keys
#    → New SSH key → Key type: Signing Key), or:
gh auth refresh -h github.com -s admin:ssh_signing_key
gh ssh-key add ~/.ssh/id_ed25519.pub --type signing -t "cometweb-signing"

# 3. Configure Git locally for this clone
cd platforms/agent-skills
git config gpg.format ssh
git config user.signingkey ~/.ssh/id_ed25519.pub
git config commit.gpgsign true
git config tag.gpgsign true

# 4. Verify
git commit --allow-empty -m "chore: verify signed commit"
git log -1 --show-signature
```

## After keys are registered

Update the Protect main ruleset to include:

```text
require signed commits: true
```

Until then, treat unsigned commits on `main` as an accepted residual risk that
package attestation (Sigstore via `attest-packages.yml`) partially covers for
release artifacts only.

"""Detection rules of the public-safety gate.

Every credential and address below is synthetic and assembled from fragments
at run time, so this file never contains, as a literal, anything the gate is
meant to stop. Addresses that must pass use RFC 2606 / RFC 6761 names.
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
import public_safety as safety


def rules(blob: bytes, *, public: bool = True) -> set[str]:
    return {item["rule"] for item in safety.check_blob("notes.md", blob, public=public)}


@pytest.mark.parametrize(("rule", "secret"), [
    ("stripe-key", b"rk_" + b"live_" + b"Q" * 24),
    ("stripe-key", b"pk_" + b"live_" + b"Q" * 24),
    ("stripe-key", b"whsec" + b"_" + b"Q" * 32),
    ("registry-token", b"npm" + b"_" + b"Q" * 36),
    ("registry-token", b"pypi-" + b"AgEIcHlwaS5vcmc" + b"Q" * 60),
    ("registry-token", b"glpat" + b"-" + b"Q" * 20),
    ("huggingface-token", b"hf" + b"_" + b"Q" * 34),
    ("slack-app-token", b"xapp" + b"-1-" + b"Q" * 12),
    ("azure-storage-key", b"Account" + b"Key=" + b"Q" * 64 + b"=="),
    ("jwt", b"ey" + b"J" + b"hbGciOiJIUzI1NiJ9" + b".ey" + b"J" + b"zdWIiOiIxMjM0NTY3ODkwIn0" + b"." + b"Q" * 43),
])
def test_credential_shapes_are_caught_without_echo(tmp_path, rule, secret):
    (tmp_path / "config.txt").write_bytes(b"value = " + secret + b"\n")
    findings = safety.scan(tmp_path)
    assert rule in {item["rule"] for item in findings}
    assert secret.decode() not in json.dumps(findings)


@pytest.mark.parametrize("secret", [
    b"rk_" + b"live_" + b"Q" * 24,
    b"npm" + b"_" + b"Q" * 36,
    b"ey" + b"J" + b"hbGciOiJIUzI1NiJ9" + b".ey" + b"J" + b"zdWIiOiIxMjM0NTY3ODkwIn0" + b"." + b"Q" * 43,
])
def test_credentials_still_block_private_packages(secret):
    assert rules(secret, public=False)


@pytest.mark.parametrize("text", [
    b"pk_test_" + b"Q" * 24,  # Stripe test-mode publishable keys are documented as safe to share
    b"npm_install_hint",
    b"hf_hub_download(repo_id)",
    b"eyJhbGciOiJIUzI1NiJ9 is only a header",
    b"see AccountKey= in the portal",
])
def test_credential_lookalikes_pass(text):
    assert not rules(text) & {
        "stripe-key", "registry-token", "huggingface-token", "slack-app-token", "azure-storage-key", "jwt",
    }


@pytest.mark.parametrize("path", [
    b"/Users/" + b"jkowalski" + b"/Projects/app/.env",
    b"/home/" + b"jkowalski" + b"/.ssh/config",
    b"C:\\" + b"Users\\" + b"jkowalski" + b"\\Desktop\\notes.txt",
    b"C:\\\\" + b"Users\\\\" + b"Jan Kowalski" + b"\\\\AppData",
])
def test_home_directories_reveal_the_account(path):
    findings = safety.check_blob("notes.md", b"first line\nopen " + path + b"\n")
    assert [(item["rule"], item["line"]) for item in findings] == [("owner-path", 2)]


@pytest.mark.parametrize("path", [
    b"/Users/you/Projects/app",
    b"/home/runner/work/agent-skills",
    b"/home/user/.config",
    b"/Users/<name>/Github/",
    b"C:\\Users\\example\\AppData",
])
def test_documentation_home_placeholders_pass(path):
    assert "owner-path" not in rules(path)


@pytest.mark.parametrize("address", [
    b"jan.kowalski" + b"@" + b"gmail.com",
    b"j.kowalski+agent" + b"@" + b"company.co.uk",
    b"maintainer" + b"@" + b"cometweb.io",
])
def test_personal_email_addresses_are_caught(address):
    assert "personal-email" in rules(b"Contact: " + address)


@pytest.mark.parametrize("address", [
    b"user@example.com",
    b"ops@mail.example.org",
    b"fixture@example.invalid",
    b"qa@shop.test",
    b"dev@app.localhost",
    b"team@acme.example",
    b"hello@cometweb.io",
    b"HELLO@CometWeb.io",
    b"12345+octocat@users.noreply.github.com",
    b"git@github.com:CometWeb-io/agent-skills.git",
    b"pytest@8.0 and actions/checkout@v7",
])
def test_reserved_and_published_addresses_pass(address):
    assert "personal-email" not in rules(address)


def test_privacy_rules_do_not_apply_to_private_packages():
    blob = b"/home/" + b"jkowalski" + b"/x and jan.kowalski" + b"@" + b"gmail.com"
    assert rules(blob) >= {"owner-path", "personal-email"}
    assert not rules(blob, public=False)


def test_one_finding_per_rule_even_after_a_placeholder(tmp_path):
    # The filter skips the placeholder and still reports the real path behind it.
    blob = b"/Users/you/a\n/Users/" + b"jkowalski" + b"/b\n/Users/" + b"akowalska" + b"/c\n"
    findings = safety.check_blob("notes.md", blob)
    assert [(item["rule"], item["line"]) for item in findings] == [("owner-path", 2)]


def test_cli_exits_nonzero_on_personal_email(tmp_path):
    (tmp_path / "README.md").write_bytes(b"Write to jan.kowalski" + b"@" + b"gmail.com\n")
    result = subprocess.run(
        [sys.executable, str(TOOLS / "public_safety.py"), "--root", str(tmp_path)], capture_output=True, text=True,
    )
    assert result.returncode == 1
    assert json.loads(result.stdout)["findings"] == [{"path": "README.md", "rule": "personal-email", "line": 1}]

"""Disposable loopback fixture, not a system sandbox or production server."""
from __future__ import annotations

from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import secrets
import sqlite3
from tempfile import TemporaryDirectory
from threading import Thread

FILES = {"/": "index.html", "/index.html": "index.html", "/policy.mjs": "policy.mjs"}


class Fixture:
    def __init__(self, directory: Path):
        self.database = directory / "records.sqlite"
        self.tokens = {secrets.token_urlsafe(32): owner for owner in ("owner", "other")}
        with self.connect() as db:
            db.execute("CREATE TABLE records (id TEXT PRIMARY KEY, owner TEXT NOT NULL, "
                       "payload TEXT NOT NULL, deleted INTEGER NOT NULL DEFAULT 0)")

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.database, timeout=3)
        try:
            with db:
                yield db
        finally:
            db.close()

    def token(self, owner="owner"):
        return next(token for token, principal in self.tokens.items() if principal == owner)

    def start(self):
        fixture = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass  # Test bearer tokens and request paths do not belong in logs.

            def reply(self, status, value):
                body = json.dumps(value, allow_nan=False).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):
                path = self.path.split("?", 1)[0]
                if path in FILES:
                    body = Path(__file__).with_name(FILES[path]).read_bytes()
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html" if path != "/policy.mjs" else "text/javascript")
                    self.send_header("Content-Length", str(len(body)))
                    self.send_header("Cache-Control", "no-store")
                    self.end_headers()
                    self.wfile.write(body)
                    return
                self.record()

            def do_PUT(self):
                self.record()

            def do_DELETE(self):
                self.record()

            def record(self):
                owner = fixture.tokens.get(self.headers.get("Authorization", "").removeprefix("Bearer "))
                if not owner or self.headers.get("Authorization") != f"Bearer {fixture.token(owner)}":
                    self.reply(401, {"error": "unauthorized"})
                    return
                match = re.fullmatch(r"/records/([a-f0-9]{32})", self.path)
                if not match:
                    self.reply(404, {"error": "not found"})
                    return
                payload = None
                if self.command == "PUT":
                    try:
                        size = int(self.headers.get("Content-Length", "0"))
                        if not 0 < size <= 2048 or self.headers.get("Content-Type") != "application/json":
                            raise ValueError("invalid body")
                        value = json.loads(self.rfile.read(size))
                        validate_quote(value)
                        payload = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
                    except (ValueError, TypeError, UnicodeDecodeError):
                        self.reply(400, {"error": "invalid quote"})
                        return
                with fixture.connect() as db:
                    # Serialize lookup + insert; retries and competing requests share one key.
                    db.execute("BEGIN IMMEDIATE")
                    row = db.execute("SELECT owner, payload, deleted FROM records WHERE id = ?", (match[1],)).fetchone()
                    if row and row[0] != owner:
                        self.reply(404, {"error": "not found"})
                    elif self.command == "PUT":
                        if row and row[2]:
                            self.reply(410, {"error": "deleted operation"})
                        elif row and row[1] != payload:
                            self.reply(409, {"error": "conflicting retry"})
                        else:
                            if not row:
                                db.execute("INSERT INTO records (id, owner, payload) VALUES (?, ?, ?)",
                                           (match[1], owner, payload))
                            db.commit()  # Commit precedes acknowledgement, including a lost response.
                            self.reply(200 if row else 201, {"id": match[1], "quote": json.loads(payload)})
                    elif not row or row[2]:
                        self.reply(404, {"error": "not found"})
                    elif self.command == "DELETE":
                        db.execute("UPDATE records SET deleted = 1 WHERE id = ?", (match[1],))
                        db.commit()
                        self.reply(200, {"id": match[1], "deleted": True})
                    else:
                        self.reply(200, {"id": match[1], "quote": json.loads(row[1])})

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.server.daemon_threads = True
        # Bound accepted socket I/O; this does not limit the host process's resources.
        original_get_request = self.server.get_request

        def get_request():
            connection, address = original_get_request()
            connection.settimeout(3)
            return connection, address

        self.server.get_request = get_request
        self.thread = Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f"http://127.0.0.1:{self.server.server_port}"
        return self

    def stop(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)


def validate_quote(value):
    if value is None:  # The policy deliberately returns null when no plan fits.
        return
    fields = {"plan", "sites", "runs", "displayedMonthly", "annualTotal"}
    if (not isinstance(value, dict) or set(value) != fields
            or value["plan"] not in {"starter", "team", "portfolio"}
            or any(type(value[key]) is not int or not 0 < value[key] <= 2**53 - 1 for key in fields - {"plan"})):
        raise ValueError("invalid quote")


@contextmanager
def disposable_fixture():
    with TemporaryDirectory(prefix="qa-repair-retest-") as directory:
        fixture = Fixture(Path(directory)).start()
        try:
            yield fixture
        finally:
            fixture.stop()

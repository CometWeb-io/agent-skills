# Cases for ../python.yml, checked by `semgrep --test` (tooling/sast.py).
# This file is test data: it is never imported or executed.
import os
import tarfile
import tempfile
import urllib.request
import zipfile
from pathlib import Path


def predictable(path: Path, data: str) -> None:
    # ruleid: cw-predictable-temp-path
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(data)
    # ruleid: cw-predictable-temp-path
    path.with_suffix(".part").write_text(data)
    # ruleid: cw-predictable-temp-path
    path.with_name(path.name + ".new").write_text(data)
    # ruleid: cw-predictable-temp-path
    open(str(path) + ".tmp", "w").close()
    # ok: cw-predictable-temp-path
    local = path.with_name(path.stem + ".local" + path.suffix)
    # ok: cw-predictable-temp-path
    fd, name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    os.replace(name, local)
    os.close(fd)


def archives(archive: Path, out: Path) -> None:
    with zipfile.ZipFile(archive) as zf:
        # ruleid: cw-archive-extractall
        zf.extractall(out)
    with tarfile.open(archive) as tf:
        # ruleid: cw-archive-extractall
        tf.extractall(out)
        # ok: cw-archive-extractall
        tf.extractall(out, filter="data")


def fetch(url: str) -> bytes:
    # ruleid: cw-urlopen-without-timeout
    urllib.request.urlopen(url).read()
    # ok: cw-urlopen-without-timeout
    with urllib.request.urlopen(url, timeout=30) as response:
        return response.read()

"""Record collection before filtering; consumers require every collected case in JUnit."""
import json
from pathlib import Path

import pytest
from _pytest.junitxml import bin_xml_escape, mangle_test_address


def pytest_addoption(parser):
    parser.addoption("--collection-manifest", required=True)


@pytest.hookimpl(wrapper=True, tryfirst=True)
def pytest_collection_modifyitems(config, items):
    def identities():
        result = []
        for item in items:
            # Use pytest's own JUnit encoding, including parameter and class names.
            names = mangle_test_address(item.nodeid)
            prefix = config.getoption("junitprefix")
            cls = ".".join(([prefix] if prefix else []) + names[:-1])
            result.append(cls + "::" + bin_xml_escape(names[-1]))
        return result

    collected = identities()
    result = yield
    with Path(config.getoption("collection_manifest")).open("x", encoding="utf-8") as handle:
        json.dump({"schema": "cometweb.pytest-collection/v1", "collected": collected, "selected": identities()}, handle)
    return result

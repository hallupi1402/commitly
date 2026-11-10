import re

from commitly.app import create_app


def test_generated_openapi_contains_contract_operations() -> None:
    contract = open("specs/001-work-journal/contracts/openapi.yaml", encoding="utf-8").read()
    expected = set()
    current_path = None
    for line in contract.splitlines():
        path_match = re.match(r"^  (/[^:]+):$", line)
        if path_match:
            current_path = path_match.group(1)
        method_match = re.match(r"^    (get|put|post|patch|delete):$", line)
        if method_match and current_path:
            expected.add((method_match.group(1).upper(), current_path))
    actual = {
        (method.upper(), path.removeprefix("/api/v1"))
        for path, operations in create_app().openapi()["paths"].items()
        for method in operations
    }
    assert expected <= actual

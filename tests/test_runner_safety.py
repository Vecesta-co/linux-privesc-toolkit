from pathlib import Path

import pytest

from privesc.runner import RunnerError, _validate


def test_runner_accepts_only_expected_read_only_commands():
    _validate(["uname", "-r"])
    _validate(["sudo", "-n", "-l"])
    _validate(["find", "/", "-type", "f", "-perm", "/6000", "-printf", "%m:%p\\0"])
    _validate(["find", "--version"])


@pytest.mark.parametrize("argv", [
    ["sh", "-c", "id"],
    ["find", "/", "-type", "f", "-perm", "/6000", "-exec", "id", ";"],
    ["find", "/", "-type", "f", "-perm", "/6000", "-exec", "id", "-printf", "%p\\0"],
    ["find", "/", "-type", "f", "-perm", "/6000", "-delete"],
    ["find", "/", "-type", "f", "-perm", "/6000", "-fprint", "/tmp/out"],
    ["sudo", "-l"],
    ["sudo", "-n", "-l", "-U", "user", "-S"],
])
def test_runner_rejects_non_allowlisted_or_dangerous_arguments(argv):
    with pytest.raises(RunnerError):
        _validate(argv)


def test_static_source_has_no_system_mutation_or_shell_execution():
    source_root = Path(__file__).parents[1] / "privesc"
    source = "\n".join(path.read_text(encoding="utf-8") for path in source_root.rglob("*.py"))
    forbidden = ["shell" + "=" + "True", "os." + "system(", "os." + "setuid(", "." + "chmod(", "os." + "remove(", "rmtree("]
    for pattern in forbidden:
        assert pattern not in source

import time

import pytest

from scripts.runner import CmdClick, CmdLoop, CmdWait, ScriptRunner, parse_script


def test_parse_basic():
    cmds = parse_script("move 1 2\nclick left\nwait 10\nkey SPACE\n# c\n")
    assert len(cmds) == 4
    assert isinstance(cmds[1], CmdClick) and cmds[1].button == "left"
    assert isinstance(cmds[2], CmdWait) and cmds[2].ms == 10


def test_parse_loop():
    cmds = parse_script("loop 3\n  click\n  wait 1\nend")
    assert isinstance(cmds[0], CmdLoop) and cmds[0].count == 3 and len(cmds[0].body) == 2


@pytest.mark.parametrize(
    "src",
    ["end", "loop 2\nclick", "bogus", "click nope", "loop 0\nend", "wait -1", "key ????"],
)
def test_parse_errors(src):
    with pytest.raises(ValueError):
        parse_script(src)


def test_run_executes(null_input):
    runner = ScriptRunner()
    assert runner.run("loop 2\nclick 5 6\nend\nkey A")
    deadline = time.time() + 3
    while runner.is_running() and time.time() < deadline:
        time.sleep(0.01)
    assert not runner.is_running()
    kinds = [c[0] for c in null_input.recorded()]
    assert kinds.count("click") == 2
    assert "key_down" in kinds and "key_up" in kinds
    assert runner.last_error() is None

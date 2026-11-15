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


def _run(runner, src, timeout=3):
    assert runner.run(src), runner.last_error()
    deadline = time.time() + timeout
    while runner.is_running() and time.time() < deadline:
        time.sleep(0.005)
    assert not runner.is_running()


def test_error_has_code_and_line():
    runner = ScriptRunner()
    assert runner.run("click\nmove a b") is False
    err = runner.last_error()
    assert err["code"] == "script.badNumber" and err["params"]["line"] == 2


def test_current_line_is_reported(null_input):
    runner = ScriptRunner()
    assert runner.run("click\nwait 300\nclick")
    time.sleep(0.1)
    assert runner.current_line() == 2
    runner.stop()


def test_new_commands(null_input):
    runner = ScriptRunner()
    _run(runner, 'dclick 3 4\nscroll -2\nkey CTRL+C\ntype "olá mundo"\ndrag 0 0 10 10\nwait 1-3')
    rec = null_input.recorded()
    assert rec.count(("click", "left")) == 2
    assert ("scroll", -2, 0) in rec
    i_ctrl = rec.index(("key_down", 0x11))
    assert rec[i_ctrl + 1] == ("key_down", ord("C"))
    assert rec[i_ctrl + 2] == ("key_up", ord("C"))
    assert ("type", "olá mundo") in rec
    assert ("down", "left") in rec and ("up", "left") in rec
    assert ("move", 10, 10) in rec
    assert runner.last_error() is None


def test_stop_during_drag_releases_button(null_input):
    runner = ScriptRunner()
    assert runner.run("drag 0 0 100 100\nwait 5000")
    time.sleep(0.05)
    runner.stop()
    rec = null_input.recorded()
    assert rec.count(("down", "left")) == rec.count(("up", "left")) == 1


@pytest.mark.parametrize("src", ["wait 5-", "scroll x", "drag 1 2 3", "type", "key CTRL+???"])
def test_new_command_errors(src):
    with pytest.raises(ValueError):
        parse_script(src)

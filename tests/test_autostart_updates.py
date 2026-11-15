import plistlib

import pytest

from app import autostart, updates


def test_linux_autostart_file(tmp_path):
    cmd = ["/opt/Clickr App/Clickr", "--minimized"]
    assert autostart.is_enabled("linux", tmp_path) is False
    autostart.set_enabled(True, "linux", tmp_path, cmd)
    path = tmp_path / ".config" / "autostart" / "clickr.desktop"
    text = path.read_text(encoding="utf-8")
    assert 'Exec="/opt/Clickr App/Clickr" --minimized' in text
    assert autostart.is_enabled("linux", tmp_path) is True
    autostart.set_enabled(False, "linux", tmp_path, cmd)
    assert not path.exists()
    autostart.set_enabled(False, "linux", tmp_path, cmd)  # idempotente


def test_macos_launch_agent(tmp_path):
    cmd = ["/Applications/Clickr.app/Contents/MacOS/Clickr", "--minimized"]
    autostart.set_enabled(True, "darwin", tmp_path, cmd)
    path = tmp_path / "Library" / "LaunchAgents" / "com.clickr.app.plist"
    data = plistlib.loads(path.read_bytes())
    assert data["ProgramArguments"] == cmd and data["RunAtLoad"] is True
    assert autostart.is_enabled("darwin", tmp_path)
    autostart.set_enabled(False, "darwin", tmp_path, cmd)
    assert not autostart.is_enabled("darwin", tmp_path)


def test_launch_command_has_minimized_flag():
    assert autostart.launch_command()[-1] == "--minimized"


@pytest.mark.parametrize(
    "candidate,current,expected",
    [("v1.2.0", "1.1.0", True), ("1.1.0", "1.1.0", False), ("v1.1", "1.1.0", False),
     ("v1.10.0", "1.9.9", True), ("v2", "1.99", True), ("lixo", "1.0", False),
     ("v1.0.9", "1.1.0", False), ("v1.2.0-beta", "1.1.0", True)],
)
def test_version_compare(candidate, current, expected):
    assert updates.is_newer(candidate, current) is expected


def test_check_latest():
    release = {"tag_name": "v1.5.0", "html_url": "https://github.com/vinimeggiotto/clickr/releases/tag/v1.5.0"}
    assert updates.check_latest("1.1.0", lambda: release) == {
        "version": "1.5.0", "url": release["html_url"],
    }
    assert updates.check_latest("1.5.0", lambda: release) is None
    assert updates.check_latest("1.1.0", lambda: {**release, "prerelease": True}) is None
    # Link fora do projeto nunca é repassado à UI.
    evil = {"tag_name": "v9.0.0", "html_url": "https://exemplo.invalido/baixar.exe"}
    assert updates.check_latest("1.0.0", lambda: evil)["url"] == updates.RELEASES_PAGE
    with pytest.raises(ValueError):
        updates.check_latest("1.0.0", lambda: [])

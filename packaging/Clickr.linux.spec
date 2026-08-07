# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec — gera binário Clickr (Linux)
# Uso (na raiz do repo): pyinstaller --noconfirm packaging/Clickr.linux.spec

import os

SPECDIR = os.path.dirname(os.path.abspath(SPEC))
ROOT = os.path.dirname(SPECDIR)

block_cipher = None

_icon_png = os.path.join(ROOT, 'assets', 'icon.png')
_icon = _icon_png if os.path.isfile(_icon_png) else None

a = Analysis(
    [os.path.join(ROOT, 'main.py')],
    pathex=[ROOT],
    binaries=[],
    datas=[
        (os.path.join(ROOT, 'ui'), 'ui'),
        (os.path.join(ROOT, 'assets'), 'assets'),
    ],
    hiddenimports=[
        'webview',
        'webview.platforms.gtk',
        'webview.platforms.qt',
        'pynput.keyboard._xorg',
        'pynput.mouse._xorg',
        'pystray._appindicator',
        'pystray._gtk',
        'PIL._tkinter_finder',
        'core.sendinput_pynput',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Clickr',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=_icon,
)

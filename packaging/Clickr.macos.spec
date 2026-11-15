# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec — gera Clickr.app (macOS)
# Uso (na raiz do repo): pyinstaller --noconfirm packaging/Clickr.macos.spec

import os

SPECDIR = os.path.dirname(os.path.abspath(SPEC))
ROOT = os.path.dirname(SPECDIR)

block_cipher = None

_icon_icns = os.path.join(ROOT, 'assets', 'icon.icns')
_icon = _icon_icns if os.path.isfile(_icon_icns) else None

a = Analysis(
    [os.path.join(ROOT, 'main.py')],
    pathex=[ROOT],
    binaries=[],
    datas=[
        (os.path.join(ROOT, 'ui'), 'ui'),
        (os.path.join(ROOT, 'assets'), 'assets'),
        (os.path.join(ROOT, 'VERSION'), '.'),
    ],
    hiddenimports=[
        'hotkeys.backend_pynput',
        'app.tray',
        'webview',
        'webview.platforms.cocoa',
        'pynput.keyboard._darwin',
        'pynput.mouse._darwin',
        'pystray._darwin',
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
    [],
    exclude_binaries=True,
    name='Clickr',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=_icon,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='Clickr',
)

app = BUNDLE(
    coll,
    name='Clickr.app',
    icon=_icon,
    bundle_identifier='com.clickr.app',
    info_plist={
        'NSHighResolutionCapable': True,
        'LSPrincipalClass': 'NSApplication',
        'NSAppleEventsUsageDescription': 'Clickr precisa controlar o sistema para enviar cliques e ler a janela ativa.',
    },
)

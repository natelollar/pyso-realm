# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

# Get the current working directory
base_dir = Path.cwd().parent

# Use relative path from base directory
main_script = base_dir / '__main__.py'
# Resources directory
resources_dir = base_dir / 'res'

# game_app.spec
block_cipher = None

a = Analysis(  # noqa: F821
    [str(main_script)],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Add all resources as data
a.datas += Tree(str(resources_dir), prefix='res')  # noqa: F821

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)  # noqa: F821

exe = EXE(  # noqa: F821
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='rpg_game',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    onefile=True,  # Add this line for a single executable file
)

"""
# Creates .exe that starts faster but requires entire '/dist/rpg_game' folder.
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='rpg_game',
)
"""
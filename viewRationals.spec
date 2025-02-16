# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(
    ['src\\viewRationals\\viewRationals.py'],
    pathex=['src\\viewRationals'],
    binaries=[
	],
    datas=[
		('.\\src\\viewRationals\\settings.txt', '.'),
		('.\\src\\viewRationals\\config.json', '.'),
		('.\\src\\viewRationals\\NotoMono-Regular.ttf', '.'),
		('C:\\Python310\\Lib\\site-packages\\madcad\\shaders\\*.*', '.\\madcad\\shaders'),
		('C:\\Python310\\Lib\\site-packages\\madcad\\textures\\*.*', '.\\madcad\\textures'),
		('C:\\Python310\\Lib\\site-packages\\freetype\*.*', '.\\freetype'),
	],
    hiddenimports=['madcad', 'glcontext', 'PyQt5', 'sip'],
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
    [('v', None, 'OPTION')],
    name='View Rationals',
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
	icon='icons/ojo-naturalista.ico'
)

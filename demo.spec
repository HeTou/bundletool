# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['demo-version2.py'],  # 主程序入口
    pathex=[],
    binaries=[],
    # 打包 bundletool JAR 到应用内部（只读资源）
    datas=[('bundletool-all-1.18.2.jar', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='AAB转APK工具',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,  # GUI 应用，不显示控制台
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='AAB转APK工具',
)

app = BUNDLE(
    coll,
    name='AAB转APK工具.app',
    icon=None,
    bundle_identifier='com.bundletool.gui',
    info_plist={
        'NSHighResolutionCapable': True,
        'LSUIElement': False,
    },
)

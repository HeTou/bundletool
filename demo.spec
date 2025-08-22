# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['demo-version2.py'],  # 主程序入口
    pathex=[],
    binaries=[],
    # {{ 新增：包含bundletool JAR文件 }}
    datas=[('bundletool-all-1.18.1.jar', '.')],  # 将JAR文件打包到根目录
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
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='AAB转APK工具',  # 应用名称
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # 启用压缩
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 关闭控制台窗口（GUI应用）
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # {{ 可选：添加应用图标（需准备.ico文件） }}
    # icon='app_icon.ico',
)

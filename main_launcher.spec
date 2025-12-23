import sys
import os
import PyQt5


# 在 a = Analysis(...) 部分，修改 datas 列表
a = Analysis(
    ['main_launcher.py'],
    pathex=[],
    binaries=[],
    hiddenimports=['PyQt5.QtCore', 'PyQt5.QtGui', 'PyQt5.QtWidgets', 'openpyxl'],
    datas=[
        # 包含 PyQt5 插件（解决界面控件消失问题）
        (os.path.join(os.path.dirname(PyQt5.__file__), 'Qt5', 'plugins', 'platforms'), 'PyQt5/Qt5/plugins/platforms'),
        (os.path.join(os.path.dirname(PyQt5.__file__), 'Qt5', 'plugins', 'styles'), 'PyQt5/Qt5/plugins/styles'),

        # 包含你的资源文件：格式为 (源路径, 目标文件夹)
        # 将 config.json 打包到 exe 同级目录
        ('config.json', '.'),
        # 将 README.md 打包到 exe 同级目录
        ('README.md', '.'),
        # 将 requirements.txt 打包到 exe 同级目录
        ('requirements.txt', '.'),
        # 如果你有图标文件，也需要包含
        ('cat.ico', '.'),
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# 如果你希望最终生成一个文件夹而非单个exe（方便管理资源），
# 可以将下面的 `EXE` 和 `COLLECT` 部分注释掉，或调整输出方式。
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='AI生成测试用例',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True, # 使用UPX压缩，可以减小体积，但可能增加杀毒软件误报
    runtime_tmpdir=None,
    console=False, # 与 --noconsole 对应
    icon='cat.ico' # 如果你的图标文件已经包含在 datas 里，这里只需写文件名
)
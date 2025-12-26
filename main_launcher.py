import sys
import os

if hasattr(sys, 'frozen'):
    os.environ['PATH'] = sys._MEIPASS + ";" + os.environ['PATH']
import subprocess
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QMessageBox,
                             QProgressBar, QFrame, QGridLayout)
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtGui import QFont, QIcon

# 定义样式表
STYLESHEET = """
    QMainWindow {
        background-color: #f0f2f5;
    }
    QWidget {
        font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
        color: #333;
    }
    QFrame#CardFrame {
        background-color: white;
        border-radius: 12px;
    }
    QPushButton {
        border: none;
        border-radius: 8px;
        padding: 12px;
        font-weight: bold;
        color: white;
    }
    QPushButton:hover {
        opacity: 0.9;
    }
    QPushButton:pressed {
        padding-top: 13px; /* 按下效果 */
    }
    QPushButton#LaunchBtn {
        background-color: #1890ff; /* Ant Design Blue */
        font-size: 16px;
        padding: 16px;
    }
    QPushButton#InstallBtn {
        background-color: #52c41a; /* Green */
    }
    QPushButton#DocBtn {
        background-color: #722ed1; /* Purple */
    }
    QPushButton#ExitBtn {
        background-color: #ff4d4f; /* Red */
    }
    QLabel#Title {
        color: #1890ff;
    }
    QLabel#Status {
        color: #8c8c8c;
        font-size: 12px;
    }
    QLabel#Copyright {
        color: #bfbfbf;
        font-size: 10px;
    }
"""


class InstallThread(QThread):
    """安装依赖的工作线程"""
    finished = pyqtSignal(bool, str)
    progress = pyqtSignal(str)

    def __init__(self):
        super().__init__()

    def run(self):
        try:
            self.progress.emit("正在检查pip...")
            try:
                import pip
            except ImportError:
                self.finished.emit(False, "未找到pip，请先安装Python和pip")
                return

            self.progress.emit("正在安装依赖包...")
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
                capture_output=True,
                text=True,
                encoding='utf-8'
            )

            if result.returncode == 0:
                self.finished.emit(True, "依赖包安装成功！")
            else:
                error_msg = f"安装失败：\n{result.stderr}"
                self.finished.emit(False, error_msg)

        except Exception as e:
            self.finished.emit(False, f"安装过程中出错：{str(e)}")


class LauncherGUI(QMainWindow):
    """启动器GUI界面"""

    def __init__(self):
        super().__init__()
        self.enhanced_window = None
        self.initUI()

    def initUI(self):
        """初始化界面"""
        self.setWindowTitle('大模型AI 测试用例生成工具')
        self.setGeometry(300, 200, 600, 450)
        self.setStyleSheet(STYLESHEET)

        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(20)

        # 标题
        title_label = QLabel('大模型AI 测试用例生成工具')
        title_label.setObjectName("Title")
        title_font = QFont()
        title_font.setPointSize(26)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        # 副标题
        subtitle_label = QLabel('AI 驱动的自动化测试用例生成方案')
        subtitle_label.setStyleSheet("color: #595959; margin-bottom: 10px;")
        subtitle_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(subtitle_label)

        # 主卡片区域
        card_frame = QFrame()
        card_frame.setObjectName("CardFrame")
        card_layout = QVBoxLayout(card_frame)
        card_layout.setContentsMargins(30, 30, 30, 30)
        card_layout.setSpacing(20)

        # 启动按钮
        self.enhanced_btn = QPushButton('🚀 启动大模型AI测试用例生成工具 增强版')
        self.enhanced_btn.setObjectName("LaunchBtn")
        self.enhanced_btn.setCursor(Qt.PointingHandCursor)
        self.enhanced_btn.clicked.connect(self.launchEnhancedVersion)
        card_layout.addWidget(self.enhanced_btn)

        # 分割线
        line = QLabel()
        line.setFrameStyle(QFrame.HLine | QFrame.Sunken)
        line.setStyleSheet("background-color: #f0f0f0; max-height: 1px;")
        card_layout.addWidget(line)

        # 功能按钮网格布局
        grid_layout = QGridLayout()
        grid_layout.setSpacing(15)

        # 安装依赖
        self.install_btn = QPushButton('📦 安装依赖包')
        self.install_btn.setObjectName("InstallBtn")
        self.install_btn.setCursor(Qt.PointingHandCursor)
        self.install_btn.clicked.connect(self.installRequirements)
        grid_layout.addWidget(self.install_btn, 0, 0)

        # 查看文档
        self.docs_btn = QPushButton('📖 查看说明文档')
        self.docs_btn.setObjectName("DocBtn")
        self.docs_btn.setCursor(Qt.PointingHandCursor)
        self.docs_btn.clicked.connect(self.viewDocumentation)
        grid_layout.addWidget(self.docs_btn, 0, 1)

        # 退出
        self.exit_btn = QPushButton('🚪 退出程序')
        self.exit_btn.setObjectName("ExitBtn")
        self.exit_btn.setCursor(Qt.PointingHandCursor)
        self.exit_btn.clicked.connect(self.close)
        grid_layout.addWidget(self.exit_btn, 0, 2)

        card_layout.addLayout(grid_layout)

        # 状态区域
        status_layout = QHBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: #f5f5f5;
                border-radius: 5px;
                height: 6px;
            }
            QProgressBar::chunk {
                background-color: #1890ff;
                border-radius: 5px;
            }
        """)

        self.status_label = QLabel('就绪')
        self.status_label.setObjectName("Status")
        self.status_label.setAlignment(Qt.AlignCenter)

        status_layout.addWidget(self.progress_bar)
        card_layout.addWidget(self.status_label)

        main_layout.addWidget(card_frame)

        # 版权信息
        copyright_label = QLabel('© 2024 大模型AI 测试用例生成工具 v2.0')
        copyright_label.setObjectName("Copyright")
        copyright_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(copyright_label)

        # 初始化依赖状态
        self.checkDependencies()

    def checkDependencies(self):
        """检查依赖包状态"""
        try:
            import PyQt5
            import pandas
            import openai
            self.status_label.setText('✅ 所有依赖包已安装')
            self.status_label.setStyleSheet("color: #52c41a; font-weight: bold; font-size: 12px;")
            return True
        except ImportError as e:
            missing_module = str(e).split("'")[1] if "'" in str(e) else str(e)
            self.status_label.setText(f'⚠️ 缺少依赖包: {missing_module}')
            self.status_label.setStyleSheet("color: #faad14; font-weight: bold; font-size: 12px;")
            return False

    def launchEnhancedVersion(self):
        """启动增强版本"""
        if not self.checkDependencies():
            reply = QMessageBox.question(
                self,
                '缺少依赖',
                '检测到缺少必要的依赖包，是否现在安装？',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            if reply == QMessageBox.Yes:
                self.installRequirements()
            return

        try:
            self.hide()
            import deepseek_test_generator_gui_enhanced as enhanced_module
            self.enhanced_window = enhanced_module.TestGeneratorGUI()
            self.enhanced_window.destroyed.connect(self.onEnhancedWindowClosed)
            self.enhanced_window.show()
        except Exception as e:
            QMessageBox.critical(self, '启动失败', f'无法启动增强版本：{str(e)}')
            self.show()

    def onEnhancedWindowClosed(self):
        """增强版窗口关闭时的处理"""
        self.enhanced_window = None
        self.show()
        self.checkDependencies()

    def installRequirements(self):
        """安装依赖包"""
        self.install_btn.setEnabled(False)
        self.install_btn.setText("⏳ 安装中...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.status_label.setText('正在安装依赖包，请稍候...')

        self.install_thread = InstallThread()
        self.install_thread.finished.connect(self.onInstallFinished)
        self.install_thread.progress.connect(self.onInstallProgress)
        self.install_thread.start()

    def onInstallProgress(self, message):
        self.status_label.setText(message)

    def onInstallFinished(self, success, message):
        self.install_btn.setEnabled(True)
        self.install_btn.setText("📦 安装依赖包")
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 100)

        if success:
            self.status_label.setText('✅ 依赖包安装成功！')
            self.status_label.setStyleSheet("color: #52c41a; font-weight: bold; font-size: 12px;")
            QMessageBox.information(self, '安装成功', '依赖包已成功安装！')
            self.checkDependencies()
        else:
            self.status_label.setText('❌ 依赖包安装失败')
            self.status_label.setStyleSheet("color: #ff4d4f; font-weight: bold; font-size: 12px;")
            QMessageBox.critical(self, '安装失败', message)

    def viewDocumentation(self):
        """查看说明文档"""
        readme_path = 'README.md'
        if not os.path.exists(readme_path):
            try:
                with open(readme_path, 'w', encoding='utf-8') as f:
                    f.write("""# 大模型AI 测试用例生成工具

## 简介
这是一个基于大模型AI API的测试用例生成工具，可以帮助测试人员快速生成详细的测试用例。

## 功能特点
- 支持多种测试用例模板
- 自动生成测试步骤和预期结果
- 支持Excel格式导出
- 可配置的API参数

## 使用方法
1. 在API设置页面配置您的Deepseek API信息
2. 在需求页面输入待测试的需求内容
3. 点击生成按钮创建测试用例
4. 导出为Excel文件

## 依赖包
- PyQt5: GUI界面库
- pandas: 数据处理库
- openai: API调用库

## 注意事项
请确保您有可用的Deepseek API密钥。
""")
            except Exception as e:
                QMessageBox.critical(self, '错误', f'无法创建README文件：{str(e)}')
                return

        try:
            if sys.platform == 'win32':
                os.startfile(readme_path)
            elif sys.platform == 'darwin':
                subprocess.run(['open', readme_path])
            else:
                subprocess.run(['xdg-open', readme_path])
        except Exception as e:
            try:
                with open(readme_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                from PyQt5.QtWidgets import QDialog, QTextBrowser, QVBoxLayout
                dialog = QDialog(self)
                dialog.setWindowTitle('README.md')
                dialog.resize(600, 500)
                layout = QVBoxLayout(dialog)
                text_browser = QTextBrowser()
                text_browser.setPlainText(content)
                layout.addWidget(text_browser)
                dialog.exec_()
            except Exception as e2:
                QMessageBox.critical(self, '错误', f'无法打开文档：{str(e2)}')


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    launcher = LauncherGUI()
    launcher.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
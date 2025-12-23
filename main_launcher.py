import sys
import os
if hasattr(sys, 'frozen'):
    os.environ['PATH'] = sys._MEIPASS + ";" + os.environ['PATH']
import subprocess
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QMessageBox,
                             QProgressBar, QFrame)
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtGui import QFont, QIcon


class InstallThread(QThread):
    """安装依赖的工作线程"""
    finished = pyqtSignal(bool, str)
    progress = pyqtSignal(str)

    def __init__(self):
        super().__init__()

    def run(self):
        try:
            self.progress.emit("正在检查pip...")

            # 检查pip是否可用
            try:
                import pip
            except ImportError:
                self.finished.emit(False, "未找到pip，请先安装Python和pip")
                return

            self.progress.emit("正在安装依赖包...")

            # 执行pip安装命令
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
        self.setWindowTitle('Deepseek 测试用例生成工具 - 启动器')
        self.setGeometry(300, 200, 600, 400)

        # 设置窗口图标
        try:
            self.setWindowIcon(QIcon('icon.png'))
        except:
            pass

        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)

        # 标题
        title_label = QLabel('Deepseek 测试用例生成工具')
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #2c3e50; margin-bottom: 30px;")
        layout.addWidget(title_label)

        # 版本选择区域
        version_frame = QFrame()
        version_frame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        version_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-radius: 10px;
                padding: 20px;
            }
        """)

        version_layout = QVBoxLayout(version_frame)

        # 增强版本按钮
        self.enhanced_btn = QPushButton('🚀启动 Deepseek测试用例生成工具增强版')
        self.enhanced_btn.setMinimumHeight(60)
        self.enhanced_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
                padding: 15px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #1c6ea4;
            }
        """)
        self.enhanced_btn.clicked.connect(self.launchEnhancedVersion)
        version_layout.addWidget(self.enhanced_btn)

        version_layout.addSpacing(20)

        # 功能按钮区域
        buttons_layout = QHBoxLayout()

        # 安装依赖按钮
        self.install_btn = QPushButton('📦 安装依赖包')
        self.install_btn.setMinimumHeight(50)
        self.install_btn.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)
        self.install_btn.clicked.connect(self.installRequirements)
        buttons_layout.addWidget(self.install_btn)

        # 查看文档按钮
        self.docs_btn = QPushButton('📖 查看说明文档')
        self.docs_btn.setMinimumHeight(50)
        self.docs_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
        """)
        self.docs_btn.clicked.connect(self.viewDocumentation)
        buttons_layout.addWidget(self.docs_btn)

        # 退出按钮
        self.exit_btn = QPushButton('🚪 退出程序')
        self.exit_btn.setMinimumHeight(50)
        self.exit_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        self.exit_btn.clicked.connect(self.close)
        buttons_layout.addWidget(self.exit_btn)

        version_layout.addLayout(buttons_layout)

        layout.addWidget(version_frame)

        # 状态区域
        status_frame = QFrame()
        status_layout = QVBoxLayout(status_frame)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setVisible(False)
        status_layout.addWidget(self.progress_bar)

        # 状态标签
        self.status_label = QLabel('就绪')
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        status_layout.addWidget(self.status_label)

        layout.addWidget(status_frame)

        # 版权信息
        copyright_label = QLabel('© 2024 Deepseek 测试用例生成工具 v2.0')
        copyright_label.setAlignment(Qt.AlignCenter)
        copyright_label.setStyleSheet("color: #95a5a6; font-size: 10px; margin-top: 20px;")
        layout.addWidget(copyright_label)

        # 初始化依赖状态
        self.checkDependencies()

    def checkDependencies(self):
        """检查依赖包状态"""
        try:
            import PyQt5
            import pandas
            import openai
            self.status_label.setText('✅ 所有依赖包已安装')
            self.status_label.setStyleSheet("color: #27ae60; font-size: 12px;")
            return True
        except ImportError as e:
            missing_module = str(e).split("'")[1] if "'" in str(e) else str(e)
            self.status_label.setText(f'⚠️ 缺少依赖包: {missing_module}，请点击"安装依赖包"')
            self.status_label.setStyleSheet("color: #e74c3c; font-size: 12px;")
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
            # 隐藏启动器窗口
            self.hide()

            # 导入并启动增强版GUI
            import deepseek_test_generator_gui_enhanced as enhanced_module

            # 创建增强版窗口实例
            self.enhanced_window = enhanced_module.TestGeneratorGUI()

            # 连接增强版窗口关闭信号
            self.enhanced_window.destroyed.connect(self.onEnhancedWindowClosed)

            # 显示增强版窗口
            self.enhanced_window.show()

        except Exception as e:
            QMessageBox.critical(self, '启动失败', f'无法启动增强版本：{str(e)}')
            # 重新显示启动器
            self.show()

    def onEnhancedWindowClosed(self):
        """增强版窗口关闭时的处理"""
        self.enhanced_window = None
        # 重新显示启动器窗口
        self.show()
        # 重新检查依赖状态
        self.checkDependencies()

    def installRequirements(self):
        """安装依赖包"""
        self.install_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # 忙碌状态
        self.status_label.setText('正在安装依赖包，请稍候...')

        # 创建工作线程
        self.install_thread = InstallThread()
        self.install_thread.finished.connect(self.onInstallFinished)
        self.install_thread.progress.connect(self.onInstallProgress)
        self.install_thread.start()

    def onInstallProgress(self, message):
        """安装进度更新"""
        self.status_label.setText(message)

    def onInstallFinished(self, success, message):
        """安装完成"""
        self.install_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 100)

        if success:
            self.status_label.setText('✅ 依赖包安装成功！')
            self.status_label.setStyleSheet("color: #27ae60; font-size: 12px;")
            QMessageBox.information(self, '安装成功', '依赖包已成功安装！')
            # 重新检查依赖状态
            self.checkDependencies()
        else:
            self.status_label.setText('❌ 依赖包安装失败')
            self.status_label.setStyleSheet("color: #e74c3c; font-size: 12px;")
            QMessageBox.critical(self, '安装失败', message)

    def viewDocumentation(self):
        """查看说明文档"""
        readme_path = 'README.md'

        # 检查文件是否存在
        if not os.path.exists(readme_path):
            # 创建默认的README文件
            try:
                with open(readme_path, 'w', encoding='utf-8') as f:
                    f.write("""# Deepseek 测试用例生成工具

## 简介
这是一个基于Deepseek API的测试用例生成工具，可以帮助测试人员快速生成详细的测试用例。

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

        # 尝试用系统默认程序打开文件
        try:
            if sys.platform == 'win32':
                os.startfile(readme_path)
            elif sys.platform == 'darwin':  # macOS
                subprocess.run(['open', readme_path])
            else:  # Linux
                subprocess.run(['xdg-open', readme_path])
        except Exception as e:
            # 如果打开失败，显示内容
            try:
                with open(readme_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 创建一个简单的文本查看窗口
                from PyQt5.QtWidgets import QDialog, QTextBrowser, QVBoxLayout, QPushButton

                dialog = QDialog(self)
                dialog.setWindowTitle('README.md')
                dialog.setGeometry(100, 100, 600, 500)

                layout = QVBoxLayout(dialog)

                text_browser = QTextBrowser()
                text_browser.setPlainText(content)
                layout.addWidget(text_browser)

                close_btn = QPushButton('关闭')
                close_btn.clicked.connect(dialog.close)
                layout.addWidget(close_btn)

                dialog.exec_()

            except Exception as e2:
                QMessageBox.critical(self, '错误', f'无法打开文档：{str(e2)}')


def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    # 设置应用程序样式
    app.setStyleSheet("""
        QMainWindow {
            background-color: #ecf0f1;
        }
        QLabel {
            font-family: "Microsoft YaHei", "Segoe UI";
        }
        QPushButton {
            font-family: "Microsoft YaHei", "Segoe UI";
        }
    """)

    launcher = LauncherGUI()
    launcher.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
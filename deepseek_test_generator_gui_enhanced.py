import sys
import json
import os
if hasattr(sys, 'frozen'):
    os.environ['PATH'] = sys._MEIPASS + ";" + os.environ['PATH']
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                           QHBoxLayout, QLabel, QLineEdit, QTextEdit, QPushButton,
                           QFileDialog, QMessageBox, QGroupBox, QProgressBar,
                           QSplitter, QComboBox, QCheckBox, QTabWidget, QStatusBar)
from PyQt5.QtCore import Qt, pyqtSignal, QThread
import pandas as pd
from openai import OpenAI

class WorkerThread(QThread):
    """用于后台处理的工作线程"""
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    progress = pyqtSignal(str)

    def __init__(self, api_key, base_url, model, system_prompt, user_prompt, requirements):
        super().__init__()
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.system_prompt = system_prompt
        self.user_prompt = user_prompt
        self.requirements = requirements

    def run(self):
        try:
            self.progress.emit("正在初始化API客户端...")
            client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
            )

            self.progress.emit("正在生成测试用例...")
            if self.user_prompt == '':
                tips = ""
            else:
                tips = "补充说明："
            # 构建完整的用户提示
            formatted_prompt = tips + self.user_prompt + ',\n需求如下：\n' + self.requirements

            # 调用API
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": formatted_prompt}
                ],
                temperature=0.7,
                max_tokens=8192,
                stream=True
            )

            full_response = ""
            for chunk in response:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    print(chunk.choices[0].delta.content, end="")

            # 解析响应
            result = full_response
            print(result)
            try:
                test_cases = json.loads(result)
                self.finished.emit(test_cases)
            except json.JSONDecodeError:
                # 如果不是有效的JSON，尝试提取JSON部分
                import re
                json_match = re.search(r'(\[.*\]|\{.*\})', result, re.DOTALL)
                if json_match:
                    try:
                        extracted_json = json_match.group(0)
                        test_cases = json.loads(extracted_json)
                        if isinstance(test_cases, dict) and "test_cases" in test_cases:
                            pass
                            # return test_cases["test_cases"]
                        self.finished.emit(test_cases)
                    except:
                        pass

                # 如果仍然无法解析，抛出异常
                # raise ValueError("无法从API响应中解析测试用例")
        except Exception as e:
            self.error.emit(str(e))

class TestGeneratorGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.loadConfig()
        self.initUI()

    def loadConfig(self):
        """加载配置文件"""
        import sys
        import os

        # 判断是否为打包后的环境
        if getattr(sys, 'frozen', False):
            # 打包后：文件在临时解压目录（sys._MEIPASS）
            base_path = sys._MEIPASS
        else:
            # 开发环境：使用当前工作目录
            base_path = os.path.abspath(".")

        config_path = os.path.join(base_path, 'config.json')

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            # 如果配置文件不存在，使用默认配置
            self.config = {...}  # 你的默认配置字典
            # （可选）在打包环境下创建一个默认配置文件到用户目录
            if not getattr(sys, 'frozen', False):
                with open('config.json', 'w', encoding='utf-8') as f:
                    json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            self.config = {...}  # 你的默认配置字典

    def initUI(self):
        """初始化用户界面"""
        self.setWindowTitle('Deepseek 测试用例生成工具 - 增强版')
        self.setGeometry(100, 100, 900, 700)

        # 创建中心部件和主布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 创建选项卡
        tabs = QTabWidget()
        layout.addWidget(tabs)

        # API设置选项卡
        api_tab = QWidget()
        api_layout = QVBoxLayout(api_tab)

        # API配置组
        api_group = QGroupBox("API配置")
        api_group_layout = QVBoxLayout()

        # API Key输入
        key_layout = QHBoxLayout()
        self.api_key_input = QLineEdit(self.config["api"]["api_key"])
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.show_key_btn = QPushButton("显示")
        self.show_key_btn.setCheckable(True)
        self.show_key_btn.clicked.connect(self.toggleKeyVisibility)
        key_layout.addWidget(QLabel("API Key:"))
        key_layout.addWidget(self.api_key_input)
        key_layout.addWidget(self.show_key_btn)
        api_group_layout.addLayout(key_layout)

        # Base URL输入
        base_url_layout = QHBoxLayout()
        self.base_url_input = QLineEdit(self.config["api"]["base_url"])
        base_url_layout.addWidget(QLabel("Base URL:"))
        base_url_layout.addWidget(self.base_url_input)
        api_group_layout.addLayout(base_url_layout)

        # 模型选择
        model_layout = QHBoxLayout()
        self.model_combo = QComboBox()
        self.model_combo.addItems(self.config["api"]["models"])
        self.model_combo.setCurrentText(self.config["api"]["default_model"])
        model_layout.addWidget(QLabel("模型:"))
        model_layout.addWidget(self.model_combo)
        api_group_layout.addLayout(model_layout)

        api_group.setLayout(api_group_layout)
        api_layout.addWidget(api_group)

        # 提示配置组
        prompt_group = QGroupBox("提示配置")
        prompt_group_layout = QVBoxLayout()

        # System提示
        self.system_prompt_input = QTextEdit()
        self.system_prompt_input.setPlaceholderText("输入System提示...")
        self.system_prompt_input.setText(self.config["prompts"]["system_prompt"])
        prompt_group_layout.addWidget(QLabel("System提示:"))
        prompt_group_layout.addWidget(self.system_prompt_input)

        # User提示
        self.user_prompt_input = QTextEdit()
        self.user_prompt_input.setPlaceholderText("输入相关补充内容...")
        self.user_prompt_input.setText(self.config["prompts"]["user_prompt"])
        prompt_group_layout.addWidget(QLabel("目标群体/软件介绍/补充（选填）:"))
        prompt_group_layout.addWidget(self.user_prompt_input)

        prompt_group.setLayout(prompt_group_layout)
        api_layout.addWidget(prompt_group)

        # 需求内容选项卡
        requirements_tab = QWidget()
        requirements_layout = QVBoxLayout(requirements_tab)

        self.requirements_input = QTextEdit()
        self.requirements_input.setPlaceholderText("在此输入需求内容...")
        requirements_layout.addWidget(QLabel("需求内容:"))
        requirements_layout.addWidget(self.requirements_input)

        # 输出设置选项卡
        output_tab = QWidget()
        output_layout = QVBoxLayout(output_tab)

        # 输出文件设置
        file_group = QGroupBox("输出文件")
        file_layout = QHBoxLayout()
        self.output_path = QLineEdit()
        self.output_path.setText(self.config["output"]["default_filename"])
        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self.browseOutputFile)
        file_layout.addWidget(self.output_path)
        file_layout.addWidget(browse_btn)
        file_group.setLayout(file_layout)
        output_layout.addWidget(file_group)

        # 输出选项
        options_group = QGroupBox("输出选项")
        options_layout = QVBoxLayout()

        self.include_id = QCheckBox("包含用例ID")
        self.include_id.setChecked(self.config["output"]["include_id"])
        self.include_priority = QCheckBox("包含优先级")
        self.include_priority.setChecked(self.config["output"]["include_priority"])
        self.include_precondition = QCheckBox("包含前置条件")
        self.include_precondition.setChecked(self.config["output"]["include_precondition"])

        options_layout.addWidget(self.include_id)
        options_layout.addWidget(self.include_priority)
        options_layout.addWidget(self.include_precondition)
        options_group.setLayout(options_layout)
        output_layout.addWidget(options_group)

        # 添加选项卡
        tabs.addTab(api_tab, "API设置")
        tabs.addTab(requirements_tab, "需求内容")
        tabs.addTab(output_tab, "输出设置")

        # 底部控制区域
        bottom_layout = QHBoxLayout()

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        bottom_layout.addWidget(self.progress_bar)

        # 生成按钮
        self.generate_btn = QPushButton("生成测试用例")
        self.generate_btn.clicked.connect(self.generateTestCases)
        bottom_layout.addWidget(self.generate_btn)

        layout.addLayout(bottom_layout)

        # 状态栏
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)

    def toggleKeyVisibility(self):
        """切换API Key的可见性"""
        if self.show_key_btn.isChecked():
            self.api_key_input.setEchoMode(QLineEdit.Normal)
            self.show_key_btn.setText("隐藏")
        else:
            self.api_key_input.setEchoMode(QLineEdit.Password)
            self.show_key_btn.setText("显示")

    def browseOutputFile(self):
        """浏览并选择输出文件路径"""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "选择保存位置",
            self.output_path.text(),
            "Excel文件 (*.xlsx);;所有文件 (*.*)"
        )
        if filename:
            self.output_path.setText(filename)

    def generateTestCases(self):
        """生成测试用例"""
        # 验证输入
        if not self.api_key_input.text():
            QMessageBox.warning(self, "错误", "请输入API Key")
            return

        if not self.requirements_input.toPlainText():
            QMessageBox.warning(self, "错误", "请输入需求内容")
            return

        # 禁用生成按钮
        self.generate_btn.setEnabled(False)
        self.progress_bar.setRange(0, 0)  # 显示忙碌状态
        self.statusBar.showMessage("正在生成测试用例...")

        # 创建工作线程
        self.worker = WorkerThread(
            api_key=self.api_key_input.text(),
            base_url=self.base_url_input.text(),
            model=self.model_combo.currentText(),
            system_prompt=self.system_prompt_input.toPlainText(),
            user_prompt=self.user_prompt_input.toPlainText(),
            requirements=self.requirements_input.toPlainText()
        )

        # 连接信号
        self.worker.finished.connect(self.handleTestCases)
        self.worker.error.connect(self.handleError)
        self.worker.progress.connect(self.updateProgress)

        # 启动线程
        self.worker.start()

    def handleTestCases(self, test_cases):
        """处理生成的测试用例"""
        try:
            # 准备数据
            data = []
            for idx, case in enumerate(test_cases, 1):
                steps = "\n".join([f"{i + 1}. {step}" for i, step in enumerate(case["steps"])])
                data.append({
                    "用例ID": f"TC-{idx:03d}",
                    "模块" : case["directory"],
                    "用例标题": case["title"],
                    "前置条件": "",
                    "测试步骤": steps,
                    "预期结果": case["expected_result"],
                    "优先级": "中",
                    "测试结果": "",
                    "备注": ""
                })

            # 创建DataFrame
            df = pd.DataFrame(data)

            # 根据选项调整列
            if not self.include_id.isChecked():
                df = df.drop("用例ID", axis=1)
            if not self.include_priority.isChecked():
                df = df.drop("优先级", axis=1)
            if not self.include_precondition.isChecked():
                df = df.drop("前置条件", axis=1)

            # 保存到Excel
            df.to_excel(self.output_path.text(), index=False)

            # 显示成功消息
            QMessageBox.information(
                self,
                "成功",
                f"已生成 {len(test_cases)} 个测试用例并保存到：\n{self.output_path.text()}"
            )

        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存测试用例时出错：{str(e)}")

        finally:
            # 恢复界面状态
            self.generate_btn.setEnabled(True)
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)
            self.statusBar.showMessage("就绪")

    def handleError(self, error_msg):
        """处理错误"""
        QMessageBox.critical(self, "错误", error_msg)
        self.generate_btn.setEnabled(True)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.statusBar.showMessage("出错")

    def updateProgress(self, message):
        """更新进度信息"""
        self.statusBar.showMessage(message)


def create_and_show_gui():
    """创建并显示GUI窗口（供外部调用）"""
    # 注意：这里不创建新的QApplication，使用现有的
    global app
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
        app.setStyle('Fusion')

    window = TestGeneratorGUI()
    window.show()

    # 如果这是新创建的app，启动事件循环
    if QApplication.instance().startingUp():
        sys.exit(app.exec_())
    else:
        return window


def main():
    """独立运行的主函数"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = TestGeneratorGUI()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

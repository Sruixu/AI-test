import sys
import json
import os
from PyQt5.QtGui import QFont

if hasattr(sys, 'frozen'):
    os.environ['PATH'] = sys._MEIPASS + ";" + os.environ['PATH']
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QLineEdit, QTextEdit, QPushButton,
                             QFileDialog, QMessageBox, QGroupBox, QProgressBar,
                             QSplitter, QComboBox, QCheckBox, QTabWidget, QStatusBar)
from PyQt5.QtCore import Qt, pyqtSignal, QThread
import pandas as pd
from openai import OpenAI

# 定义主程序样式表
STYLESHEET = """
    QMainWindow {
        background-color: #f0f2f5;
    }
    QWidget {
        font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
        font-size: 9pt;
        color: #333;
    }
    /* Tab Widget 样式 */
    QTabWidget::pane {
        border: 1px solid #e8e8e8;
        background: white;
        border-radius: 4px;
        top: -1px;
    }
    QTabBar::tab {
        background: #fafafa;
        border: 1px solid #e8e8e8;
        border-bottom: none;
        padding: 10px 24px;
        margin-right: 4px;
        border-top-left-radius: 6px;
        border-top-right-radius: 6px;
        color: #595959;
    }
    QTabBar::tab:selected {
        background: white;
        color: #1890ff;
        font-weight: bold;
        border-top: 2px solid #1890ff;
    }
    QTabBar::tab:hover:!selected {
        background: #e6f7ff;
        color: #1890ff;
    }

    /* 输入框样式 */
    QLineEdit, QTextEdit, QPlainTextEdit, QComboBox {
        border: 1px solid #d9d9d9;
        border-radius: 4px;
        padding: 8px;
        background: white;
        selection-background-color: #1890ff;
    }
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QComboBox:focus {
        border: 1px solid #40a9ff;
        outline: none;
    }
    QComboBox::drop-down {
        border: none;
        width: 20px;
    }
    QComboBox::down-arrow {
        image: url(none); /* 隐藏默认箭头，使用系统默认 */
    }

    /* 分组框样式 */
    QGroupBox {
        border: 1px solid #e8e8e8;
        border-radius: 6px;
        margin-top: 16px;
        padding-top: 12px;
        font-weight: bold;
        color: #262626;
        background-color: #fafafa;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 12px;
        padding: 0 6px 0 6px;
        background-color: #fafafa;
    }

    /* 按钮样式 */
    QPushButton {
        background-color: #1890ff;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 8px 20px;
        font-weight: 600;
        min-width: 80px;
    }
    QPushButton:hover {
        background-color: #40a9ff;
    }
    QPushButton:pressed {
        background-color: #096dd9;
    }
    QPushButton:disabled {
        background-color: #d9d9d9;
        color: rgba(0, 0, 0, 0.25);
    }

    /* 进度条样式 */
    QProgressBar {
        border: none;
        background-color: #f5f5f5;
        border-radius: 4px;
        height: 8px;
        text-align: center;
    }
    QProgressBar::chunk {
        background-color: #1890ff;
        border-radius: 4px;
    }

    /* 状态栏 */
    QStatusBar {
        background-color: #001529;
        color: white;
    }
    QStatusBar QLabel {
        color: white;
    }
"""


class WorkerThread(QThread):
    """用于后台处理的工作线程"""
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    progress = pyqtSignal(str)

    def __init__(self, api_key, base_url, model, system_prompt, user_prompt, requirements, service_type):
        super().__init__()
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.system_prompt = system_prompt
        self.user_prompt = user_prompt
        self.requirements = requirements
        self.service_type = service_type  # "DeepSeek", "MiMo" 或 "智普AI"

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
            formatted_prompt = tips + self.user_prompt + ',\n需求如下：\n' + self.requirements

            api_params = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": formatted_prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 16384,
                "stream": True,
            }

            if self.service_type == "MiMo":
                api_params["extra_body"] = {"thinking": {"type": "disabled"}}
                api_params["temperature"] = 0.3
                api_params["top_p"] = 0.95
            elif self.service_type == "智普AI":
                api_params["extra_body"] = {"thinking": {"type": "enabled"}}
                api_params["temperature"] = 0.7
            elif self.service_type == "Kimi":
                api_params["temperature"] = 0.6
                api_params["top_p"] = 0.95

            self.progress.emit("正在调用API，请稍候...")
            response = client.chat.completions.create(**api_params)

            full_response = ""
            for chunk in response:
                if not hasattr(chunk, 'choices') or not chunk.choices:
                    continue
                try:
                    choice = chunk.choices[0]
                    if self.service_type in ["智普AI", "Kimi"]:
                        if hasattr(choice, 'delta') and choice.delta is not None:
                            delta = choice.delta
                            if hasattr(delta, 'content') and delta.content is not None:
                                content_piece = delta.content
                                full_response += content_piece
                    else:
                        if hasattr(choice, 'delta') and choice.delta is not None:
                            delta = choice.delta
                            if hasattr(delta, 'content') and delta.content is not None:
                                content_piece = delta.content
                                full_response += content_piece
                except IndexError:
                    continue
                except Exception as e:
                    print(f"处理数据块时遇到意外错误: {e}")
                    continue

            self.progress.emit("API响应接收完成，正在解析...")

            if not full_response.strip():
                self.error.emit("API返回的响应内容为空，请检查您的请求参数和网络连接。")
                return

            print(f"原始响应预览: {full_response[:500]}...")

            try:
                test_cases = json.loads(full_response)
                self.finished.emit(test_cases)
            except json.JSONDecodeError:
                try:
                    import re
                    json_match = re.search(r'(\[.*\]|\{.*\})', full_response, re.DOTALL)
                    if json_match:
                        extracted_json = json_match.group(0)
                        test_cases = json.loads(extracted_json)
                        self.finished.emit(test_cases)
                    else:
                        self.error.emit("无法从API响应中提取有效的JSON数据。响应内容为:\n" + full_response[:1000])
                except Exception as parse_error:
                    self.error.emit(f"解析JSON数据失败: {str(parse_error)}\n原始响应开头: {full_response[:500]}")
            except Exception as e:
                self.error.emit(f"处理API响应时发生意外错误: {str(e)}")

        except Exception as e:
            self.error.emit(f"API调用失败: {str(e)}")


class TestGeneratorGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.loadConfig()
        self.initUI()

    def loadConfig(self):
        """加载配置文件"""
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(".")

        config_path = os.path.join(base_path, 'config.json')

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            self.config = {
                "api": {
                    "api_key": "",
                    "base_url": "https://api.deepseek.com/v1",
                    "models": ["deepseek-reasoner", "deepseek-chat", "qwen-plus"],
                    "default_model": "deepseek-reasoner",
                    "mimo": {
                        "base_url": "https://api.xiaomimimo.com/v1",
                        "models": ["mimo-v2-flash"],
                        "default_model": "mimo-v2-flash"
                    },
                    "zhipu": {
                        "base_url": "https://open.bigmodel.cn/api/paas/v4/",
                        "models": ["glm-4.6", "glm-4.7"],
                        "default_model": "glm-4.7"
                    },
                    "kimi": {
                        "base_url": "https://api.moonshot.cn/v1",
                        "models": ["kimi-k2-turbo-preview", "kimi-k2-thinking-turbo"],
                        "default_model": "kimi-k2-thinking-turbo"
                    }
                },
                "prompts": {
                    "system_prompt": "你是一名资深软件测试工程师，请根据以下需求生成测试用例，返回JSON格式：\n- 每个测试用例包含：directory(模块),title(标题), steps(步骤列表), expected_result(预期结果),priority(优先级，分为P0、P1、P2)\n- 要求覆盖正常情况和异常情况\n- 测试用例应该详细且具体\n- 确保测试步骤清晰可执行\n- 模块作为分类作用，方便阅读；\n- 测试用例不少于50条\n- 优先级判断标准：\n  P0：核心功能、冒烟测试用例、用于判断版本是否可测，涉及支付/安全、主要业务流程\n  P1：主要功能，保证核心功能的稳定性和正确性、涉及数据完整性\n  P2：次要功能、界面优化、异常场景、边界情况\n\n只需返回JSON数组，不要额外解释。示例格式：\n                                [{{\n                                    \"directory\": \"模块\",\n                                    \"title\": \"测试用例1\",\n                                    \"steps\": [\"步骤1\", \"步骤2\"],\n                                    \"expected_result\": \"预期结果\",\n                                    \"priority\": \"P1\"\n                                   }}],",
                    "user_prompt": ""
                },
                "output": {
                    "default_filename": "test_cases.xlsx",
                    "include_id": True,
                    "include_priority": True,
                    "include_precondition": True
                },
                "ui": {
                    "window_title": "AI大模型测试用例生成工具",
                    "window_width": 1000,
                    "window_height": 750
                }
            }
            if not getattr(sys, 'frozen', False):
                with open('config.json', 'w', encoding='utf-8') as f:
                    json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            # 使用硬编码的默认配置防止崩溃
            pass

    def initUI(self):
        """初始化用户界面"""
        self.setWindowTitle(self.config["ui"]["window_title"])
        self.setGeometry(100, 100, self.config["ui"]["window_width"], self.config["ui"]["window_height"])
        self.setStyleSheet(STYLESHEET)

        # 创建中心部件和主布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 创建选项卡
        tabs = QTabWidget()
        layout.addWidget(tabs)

        # --- API设置选项卡 ---
        api_tab = QWidget()
        api_layout = QVBoxLayout(api_tab)

        # API配置组
        api_group = QGroupBox("API 配置")
        api_group_layout = QVBoxLayout()

        # 第一行：服务选择
        service_layout = QHBoxLayout()
        service_layout.addWidget(QLabel("AI 服务:"))
        self.service_combo = QComboBox()
        self.service_combo.addItems(["DeepSeek", "MiMo", "智普AI", "Kimi"])
        self.service_combo.currentTextChanged.connect(self.onServiceChanged)
        service_layout.addWidget(self.service_combo, 1)
        api_group_layout.addLayout(service_layout)

        # 第二行：API Key
        key_layout = QHBoxLayout()
        key_layout.addWidget(QLabel("API Key:"))
        self.api_key_input = QLineEdit(self.config["api"]["api_key"])
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setPlaceholderText("请输入 API 密钥")
        key_layout.addWidget(self.api_key_input, 1)

        self.show_key_btn = QPushButton("显示")
        self.show_key_btn.setCheckable(True)
        self.show_key_btn.setFixedWidth(60)
        self.show_key_btn.clicked.connect(self.toggleKeyVisibility)
        # 覆盖样式让小按钮看起来更轻量
        self.show_key_btn.setStyleSheet("""
            QPushButton { background-color: #e6f7ff; color: #1890ff; border: 1px solid #91d5ff; }
            QPushButton:hover { background-color: #bae7ff; }
            QPushButton:checked { background-color: #1890ff; color: white; border: 1px solid #1890ff; }
        """)
        key_layout.addWidget(self.show_key_btn)
        api_group_layout.addLayout(key_layout)

        # 第三行：Base URL
        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel("Base URL:"))
        self.base_url_input = QLineEdit(self.config["api"]["base_url"])
        url_layout.addWidget(self.base_url_input, 1)
        api_group_layout.addLayout(url_layout)

        # 第四行：模型选择
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("模型:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems(self.config["api"]["models"])
        self.model_combo.setCurrentText(self.config["api"]["default_model"])
        model_layout.addWidget(self.model_combo, 1)
        api_group_layout.addLayout(model_layout)

        api_group.setLayout(api_group_layout)
        api_layout.addWidget(api_group)

        # 提示配置组
        prompt_group = QGroupBox("提示词配置")
        prompt_group_layout = QVBoxLayout()

        prompt_group_layout.addWidget(QLabel("System 提示 (角色设定):"))
        self.system_prompt_input = QTextEdit()
        self.system_prompt_input.setPlaceholderText("输入 System 提示...")
        self.system_prompt_input.setText(self.config["prompts"]["system_prompt"])
        # 设置等宽字体适合查看提示词
        self.system_prompt_input.setStyleSheet("font-family: Consolas, Monaco, monospace;")
        prompt_group_layout.addWidget(self.system_prompt_input)

        prompt_group_layout.addWidget(QLabel("User 补充 (选填):"))
        self.user_prompt_input = QTextEdit()
        self.user_prompt_input.setMaximumHeight(80)
        self.user_prompt_input.setPlaceholderText("输入相关补充内容，如目标用户群体、软件介绍等...")
        self.user_prompt_input.setText(self.config["prompts"]["user_prompt"])
        prompt_group_layout.addWidget(self.user_prompt_input)

        prompt_group.setLayout(prompt_group_layout)
        api_layout.addWidget(prompt_group)

        # --- 需求内容选项卡 ---
        requirements_tab = QWidget()
        requirements_layout = QVBoxLayout(requirements_tab)
        requirements_layout.setContentsMargins(0, 0, 0, 0)

        requirements_layout.addWidget(QLabel("需求详细内容 (支持粘贴 PRD/用户故事):"))
        self.requirements_input = QTextEdit()
        self.requirements_input.setPlaceholderText("在此输入需求内容...")
        requirements_layout.addWidget(self.requirements_input)

        # --- 输出设置选项卡 ---
        output_tab = QWidget()
        output_layout = QVBoxLayout(output_tab)

        # 输出文件设置
        file_group = QGroupBox("输出文件路径")
        file_layout = QHBoxLayout()
        self.output_path = QLineEdit()
        self.output_path.setText(self.config["output"]["default_filename"])
        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self.browseOutputFile)
        browse_btn.setFixedWidth(80)
        file_layout.addWidget(self.output_path)
        file_layout.addWidget(browse_btn)
        file_group.setLayout(file_layout)
        output_layout.addWidget(file_group)

        # 输出选项
        options_group = QGroupBox("导出选项")
        options_layout = QVBoxLayout()

        self.include_id = QCheckBox("包含用例 ID (如 TC-001)")
        self.include_id.setChecked(self.config["output"]["include_id"])
        self.include_priority = QCheckBox("包含优先级 (P0/P1/P2)")
        self.include_priority.setChecked(self.config["output"]["include_priority"])
        self.include_precondition = QCheckBox("包含前置条件")
        self.include_precondition.setChecked(self.config["output"]["include_precondition"])

        options_layout.addWidget(self.include_id)
        options_layout.addWidget(self.include_priority)
        options_layout.addWidget(self.include_precondition)
        options_group.setLayout(options_layout)
        output_layout.addWidget(options_group)
        output_layout.addStretch()

        # 添加选项卡
        tabs.addTab(api_tab, " ⚙️  API 设置")
        tabs.addTab(requirements_tab, " 📝 需求内容")
        tabs.addTab(output_tab, " 📂 输出设置")

        # 底部控制区域
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(15)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setVisible(False)
        bottom_layout.addWidget(self.progress_bar)

        # 生成按钮
        self.generate_btn = QPushButton("🚀 开始生成测试用例")
        self.generate_btn.setMinimumHeight(40)
        self.generate_btn.setFont(QFont("Arial", 11, QFont.Bold))
        self.generate_btn.clicked.connect(self.generateTestCases)
        bottom_layout.addWidget(self.generate_btn)

        layout.addLayout(bottom_layout)

        # 状态栏
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)

    def onServiceChanged(self, service):
        """当切换AI服务时，更新对应的Base URL和模型列表"""
        if service == "MiMo":
            self.base_url_input.setText(self.config["api"]["mimo"]["base_url"])
            self.model_combo.clear()
            self.model_combo.addItems(self.config["api"]["mimo"]["models"])
            self.model_combo.setCurrentText(self.config["api"]["mimo"]["default_model"])
            self.api_key_input.setText("")
            self.api_key_input.setPlaceholderText("请输入 MiMo API Key")
        elif service == "智普AI":
            self.base_url_input.setText(self.config["api"]["zhipu"]["base_url"])
            self.model_combo.clear()
            self.model_combo.addItems(self.config["api"]["zhipu"]["models"])
            self.model_combo.setCurrentText(self.config["api"]["zhipu"]["default_model"])
            self.api_key_input.setText("")
            self.api_key_input.setPlaceholderText("请输入智普AI API Key")
        elif service == "Kimi":
            self.base_url_input.setText(self.config["api"]["kimi"]["base_url"])
            self.model_combo.clear()
            self.model_combo.addItems(self.config["api"]["kimi"]["models"])
            self.model_combo.setCurrentText(self.config["api"]["kimi"]["default_model"])
            self.api_key_input.setText("")
            self.api_key_input.setPlaceholderText("请输入 Kimi API Key")
        else:  # DeepSeek
            self.base_url_input.setText(self.config["api"]["base_url"])
            self.model_combo.clear()
            self.model_combo.addItems(self.config["api"]["models"])
            self.model_combo.setCurrentText(self.config["api"]["default_model"])
            self.api_key_input.setText("")
            self.api_key_input.setPlaceholderText("请输入 DeepSeek API Key")

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
        if not self.api_key_input.text():
            QMessageBox.warning(self, "错误", "请输入 API Key")
            return

        if not self.requirements_input.toPlainText():
            QMessageBox.warning(self, "错误", "请输入需求内容")
            return

        self.generate_btn.setEnabled(False)
        self.generate_btn.setText("⏳ 生成中...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.statusBar.showMessage("正在生成测试用例，请稍候...")

        current_service = self.service_combo.currentText()

        self.worker = WorkerThread(
            api_key=self.api_key_input.text(),
            base_url=self.base_url_input.text(),
            model=self.model_combo.currentText(),
            system_prompt=self.system_prompt_input.toPlainText(),
            user_prompt=self.user_prompt_input.toPlainText(),
            requirements=self.requirements_input.toPlainText(),
            service_type=current_service
        )

        self.worker.finished.connect(self.handleTestCases)
        self.worker.error.connect(self.handleError)
        self.worker.progress.connect(self.updateProgress)

        self.worker.start()

    def handleTestCases(self, test_cases):
        """处理生成的测试用例"""
        try:
            if isinstance(test_cases, dict) and "test_cases" in test_cases:
                test_cases_list = test_cases["test_cases"]
            elif isinstance(test_cases, list):
                test_cases_list = test_cases
            else:
                QMessageBox.warning(self, "警告", "API返回的数据格式不符合预期，尝试处理...")
                test_cases_list = [test_cases]

            data = []
            for idx, case in enumerate(test_cases_list, 1):
                directory = case.get("directory", "未分类模块")
                if isinstance(case.get("steps", []), list):
                    steps = "\n".join([f"{i + 1}. {step}" for i, step in enumerate(case["steps"])])
                else:
                    steps = str(case.get("steps", ""))
                priority = case.get("priority", "P1")

                data.append({
                    "用例ID": f"TC-{idx:03d}",
                    "模块": directory,
                    "用例标题": case.get("title", f"未命名用例{idx}"),
                    "前置条件": case.get("precondition", ""),
                    "测试步骤": steps,
                    "预期结果": case.get("expected_result", ""),
                    "优先级": priority,
                    "测试结果": "",
                    "备注": ""
                })

            df = pd.DataFrame(data)

            if not self.include_id.isChecked():
                df = df.drop("用例ID", axis=1)
            if not self.include_priority.isChecked():
                df = df.drop("优先级", axis=1)
            if not self.include_precondition.isChecked():
                df = df.drop("前置条件", axis=1)

            output_path = self.output_path.text()
            if not output_path.endswith('.xlsx'):
                output_path += '.xlsx'
            df.to_excel(output_path, index=False)

            QMessageBox.information(
                self,
                "成功",
                f"已生成 {len(test_cases_list)} 个测试用例并保存到：\n{output_path}"
            )

        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存测试用例时出错：{str(e)}")

        finally:
            self.generate_btn.setEnabled(True)
            self.generate_btn.setText("🚀 开始生成测试用例")
            self.progress_bar.setVisible(False)
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)
            self.statusBar.showMessage("就绪")

    def handleError(self, error_msg):
        """处理错误"""
        QMessageBox.critical(self, "错误", error_msg)
        self.generate_btn.setEnabled(True)
        self.generate_btn.setText("🚀 开始生成测试用例")
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.statusBar.showMessage("出错")

    def updateProgress(self, message):
        """更新进度信息"""
        self.statusBar.showMessage(message)


def create_and_show_gui():
    """创建并显示GUI窗口（供外部调用）"""
    global app
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
        app.setStyle('Fusion')

    window = TestGeneratorGUI()
    window.show()

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
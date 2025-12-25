import sys
import json
import os
import re

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
            # 构建完整的用户提示
            formatted_prompt = tips + self.user_prompt + ',\n需求如下：\n' + self.requirements

            # 准备API调用参数
            api_params = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": formatted_prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 40000,
                "stream": True
            }

            # 根据服务类型调整参数
            if self.service_type == "MiMo":
                # MiMo API特有参数
                api_params["extra_body"] = {"thinking": {"type": "disabled"}}
                api_params["temperature"] = 0.3
                api_params["top_p"] = 0.95
            elif self.service_type == "智普AI":
                # 智普AI特有参数
                api_params["extra_body"] = {
                    "thinking": {
                        "type": "enabled"
                    }
                }
                # 智普AI可能需要调整temperature
                api_params["temperature"] = 0.7
            elif self.service_type == "Kimi":
                # Kimi API参数 - 使用默认配置，可根据需要调整
                api_params["temperature"] = 0.6
                api_params["top_p"] = 0.95

            # 调用API
            self.progress.emit("正在调用API，请稍候...")
            response = client.chat.completions.create(**api_params)

            full_response = ""
            # 【关键修复】安全地处理流式响应，避免 index out of range
            for chunk in response:
                # 1. 检查 chunk.choices 列表是否为空
                if not hasattr(chunk, 'choices') or not chunk.choices:
                    # 这是一个可能没有内容的数据块，跳过
                    continue
                # 2. 安全地尝试获取第一个 choice
                try:
                    choice = chunk.choices[0]
                    # 3. 检查 delta 和 content 字段是否存在
                    if self.service_type in ["智普AI", "Kimi"]:
                        # 智普AI和Kimi的响应可能包含reasoning_content和content
                        if hasattr(choice, 'delta') and choice.delta is not None:
                            delta = choice.delta
                            # 如果有reasoning_content，跳过它
                            if hasattr(delta, 'content') and delta.content is not None:
                                content_piece = delta.content
                                full_response += content_piece
                    else:
                        # 其他服务的处理方式不变
                        if hasattr(choice, 'delta') and choice.delta is not None:
                            delta = choice.delta
                            if hasattr(delta, 'content') and delta.content is not None:
                                content_piece = delta.content
                                full_response += content_piece
                except IndexError:
                    # 捕获并忽略索引错误，继续处理下一个数据块
                    continue
                except Exception as e:
                    # 其他意外错误，记录但继续
                    print(f"处理数据块时遇到意外错误: {e}")
                    continue

            self.progress.emit("API响应接收完成，正在解析...")

            # 检查是否收到了有效响应
            if not full_response.strip():
                self.error.emit("API返回的响应内容为空，请检查您的请求参数和网络连接。")
                return

            # 打印原始响应前500字符便于调试（可选）
            print(f"原始响应预览: {full_response[:500]}...")

            # 解析响应
            try:
                # 首先尝试直接解析完整响应为JSON
                test_cases = json.loads(full_response)
                self.finished.emit(test_cases)
            except json.JSONDecodeError:
                # 如果直接解析失败，尝试提取响应中的JSON部分
                try:
                    import re
                    # 匹配类似 [...], {...} 的JSON结构
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
            self.config = {
                "api": {
                    "api_key": "",
                    "base_url": "https://api.deepseek.com/v1",
                    "models": ["deepseek-reasoner", "deepseek-chat"],
                    "default_model": "deepseek-reasoner",
                    "mimo": {
                        "base_url": "https://api.xiaomimimo.com/v1",
                        "models": ["mimo-v2-flash"],
                        "default_model": "mimo-v2-flash"
                    },
                    "zhipu": {
                        "base_url": "https://open.bigmodel.cn/api/paas/v4/",
                        "models": ["glm-4.7", "glm-4.6"],
                        "default_model": "glm-4.7"
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
                    "window_title": "大模型AI测试用例生成工具",
                    "window_width": 900,
                    "window_height": 700
                }
            }
            # （可选）在打包环境下创建一个默认配置文件到用户目录
            if not getattr(sys, 'frozen', False):
                with open('config.json', 'w', encoding='utf-8') as f:
                    json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            # 使用默认配置
            self.config = {...}  # 同上默认配置

    def initUI(self):
        """初始化用户界面"""
        self.setWindowTitle(self.config["ui"]["window_title"])
        self.setGeometry(100, 100, self.config["ui"]["window_width"], self.config["ui"]["window_height"])

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

        # API服务选择
        service_layout = QHBoxLayout()
        self.service_combo = QComboBox()
        self.service_combo.addItems(["DeepSeek", "MiMo", "智普AI", "Kimi"])
        self.service_combo.currentTextChanged.connect(self.onServiceChanged)
        service_layout.addWidget(QLabel("AI服务:"))
        service_layout.addWidget(self.service_combo)
        api_group_layout.addLayout(service_layout)

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

    def onServiceChanged(self, service):
        """当切换AI服务时，更新对应的Base URL和模型列表"""
        if service == "MiMo":
            self.base_url_input.setText(self.config["api"]["mimo"]["base_url"])
            self.model_combo.clear()
            self.model_combo.addItems(self.config["api"]["mimo"]["models"])
            self.model_combo.setCurrentText(self.config["api"]["mimo"]["default_model"])
            # 清空API Key输入框，提示用户输入MiMo的API Key
            self.api_key_input.setText("")
            self.api_key_input.setPlaceholderText("请输入MiMo API Key")
        elif service == "智普AI":
            self.base_url_input.setText(self.config["api"]["zhipu"]["base_url"])
            self.model_combo.clear()
            self.model_combo.addItems(self.config["api"]["zhipu"]["models"])
            self.model_combo.setCurrentText(self.config["api"]["zhipu"]["default_model"])
            # 清空API Key输入框，提示用户输入智普AI的API Key
            self.api_key_input.setText("")
            self.api_key_input.setPlaceholderText("请输入智普AI API Key")
        elif service == "Kimi":
            self.base_url_input.setText(self.config["api"]["kimi"]["base_url"])
            self.model_combo.clear()
            self.model_combo.addItems(self.config["api"]["kimi"]["models"])
            self.model_combo.setCurrentText(self.config["api"]["kimi"]["default_model"])
            self.api_key_input.setText("")
            self.api_key_input.setPlaceholderText("请输入Kimi API Key")
        else:  # DeepSeek
            self.base_url_input.setText(self.config["api"]["base_url"])
            self.model_combo.clear()
            self.model_combo.addItems(self.config["api"]["models"])
            self.model_combo.setCurrentText(self.config["api"]["default_model"])
            # 清空API Key输入框，提示用户输入DeepSeek的API Key
            self.api_key_input.setText("")
            self.api_key_input.setPlaceholderText("请输入DeepSeek API Key")

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

        # 获取当前选择的服务类型
        current_service = self.service_combo.currentText()

        # 创建工作线程
        self.worker = WorkerThread(
            api_key=self.api_key_input.text(),
            base_url=self.base_url_input.text(),
            model=self.model_combo.currentText(),
            system_prompt=self.system_prompt_input.toPlainText(),
            user_prompt=self.user_prompt_input.toPlainText(),
            requirements=self.requirements_input.toPlainText(),
            service_type=current_service  # 传递服务类型
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
            # 确保test_cases是列表格式
            if isinstance(test_cases, dict) and "test_cases" in test_cases:
                test_cases_list = test_cases["test_cases"]
            elif isinstance(test_cases, list):
                test_cases_list = test_cases
            else:
                QMessageBox.warning(self, "警告", "API返回的数据格式不符合预期，尝试处理...")
                test_cases_list = [test_cases]

            # 准备数据
            data = []
            for idx, case in enumerate(test_cases_list, 1):
                # 处理directory字段，如果不存在则使用默认值
                directory = case.get("directory", "未分类模块")

                # 确保步骤是字符串格式
                if isinstance(case.get("steps", []), list):
                    steps = "\n".join([f"{i + 1}. {step}" for i, step in enumerate(case["steps"])])
                else:
                    steps = str(case.get("steps", ""))

                # 获取优先级，如果没有则使用默认值"P1"
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
            output_path = self.output_path.text()
            if not output_path.endswith('.xlsx'):
                output_path += '.xlsx'
            df.to_excel(output_path, index=False)

            # 显示成功消息
            QMessageBox.information(
                self,
                "成功",
                f"已生成 {len(test_cases_list)} 个测试用例并保存到：\n{output_path}"
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

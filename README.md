# 大模型AI 测试用例生成工具

基于**Deepseek** 、 **MiMo (小米)**、 **智谱 (Zhipu)**  **Kimi** 及 **MiniMax** 多模型 API的测试用例生成工具，提供图形化界面，可方便地将需求转换为结构化测试用例并导出为Excel格式。。

**参考项目**：[monkey410/Ai-test](https://github.com/monkey410/Ai-test.git)

---

## ✨ 功能特点

- 🖥️ **图形化界面** - 直观易用的 PyQt5 桌面应用程序
- 🔄 **多 AI 引擎支持** - 一键切换 **Deepseek**、**MiMo (小米)**、**智谱 (Zhipu)** 、**MiniMax** 和 **Kimi** 等主流大模型。
- ⚙️ **灵活API配置** - 可自定义模型、Base URL 及调用参数
- 📝 **提示词模板化** - 可修改系统与用户提示词，适应不同测试风格
- 📊 **Excel导出** - 生成包含用例ID、模块、步骤、预期结果、优先级等字段的规范Excel文件
- 🗂️ **输出字段自定义** - 可勾选导出字段（用例ID、优先级、前置条件）

---

## 🚀 快速开始

### 环境要求
- Python 3.10 或更高版本
- 有效的 API Key（支持 Deepseek、MiMo、Zhipu、Kimi、MiniMax 任选其一或多个）

### 安装步骤

1. **克隆项目**
   ```bash
   git clone https://github.com/Sruixu/AI-test.git
   cd AI-test
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **获取API Key**
   - Deepseek Key： 访问 [Deepseek控制台](https://platform.deepseek.com/api_keys)
   - MiMo Key：访问 [MiMo开放平台](https://platform.xiaomimimo.com/#/console/api-keys) 
   - 智谱Key : 访问 [智谱AI开放平台](https://bigmodel.cn/usercenter/proj-mgmt/apikeys) 
   - Kimi Key : 访问 [Moonshot AI开放平台](https://platform.moonshot.cn/console/api-keys)
   - MiniMax Key：访问 [MiniMax开放平台](https://platform.minimaxi.com/user-center/basic-information)
4. **启动应用**
   ```bash
   python main_launcher.py
   ```
   或直接运行 test_generator_gui.py

---

## 📖 使用指南

### 第一步：API设置
在 “config.json”文件配置API_key
   ```bash
	{
	  "api": {
	    "api_key": "您的默认 API Key",
	    "base_url": "https://api.deepseek.com/v1",
	    "models": ["deepseek-reasoner", "deepseek-chat"],
	    "default_model": "deepseek-reasoner",
	    ...
	  }
	}
   ```

### 第二步：运行并设置
运行后在"需求内容"标签页中：
1. 运行程序，进入 **“API设置”** 标签页。
2. 在 **“AI服务”** 下拉框中选择本次要使用的模型（DeepSeek / MiMo /zhipu / Kimi）。
3. 界面会自动切换对应的Base URL和模型列表。
4. 在 **“API Key”** 输入框中粘贴对应服务的Key（切换服务时输入框会自动清空错误用）。

### 第三步：输入需求与提示词
1. 在 **“API设置”** 标签页的提示词区域，可调整系统指令 (System Prompt) 和补充说明 (User Prompt)。 
2. 切换到 **“需求内容”** 标签页，在文本框中粘贴或输入详细的需求描述。


### 第四步：配置输出
切换到 **“输出设置”** 标签页：
1. **选择保存路径** - 点击“浏览...”指定Excel文件存储位置。
2. **配输出选项**（勾选即包含）：  
- ✅ 包含用例ID
- ✅ 包含优先级（P0/P1/P2）
- ✅ 包含前置条件

### 第五步：生成与导出
1. 点击 **“生成测试用例”** 按钮。
2. 观察底部状态栏和进度条，工具将显示“正在调用API...”、“正在接收数据...”等状态。
3. **耐心等待**。AI生成与流式接收过程通常需要3-5分钟，请勿关闭窗口。
4. 生成完成后，会弹出提示框显示保存路径。

---

## ⚙️ 配置说明

项目使用 `config.json` 配置文件，主要包含：
```json
{
  "api": {
    "api_key": "",
    "base_url": "https://api.deepseek.com/v1",
    "models": ["deepseek-reasoner", "deepseek-chat"],
    "default_model": "deepseek-reasoner",
    "mimo": {
      "base_url": "https://api.xiaomimimo.com/v1",
      "models": ["mimo-v2-flash"],
      "default_model": "mimo-v2-flash"
    }
  }
}
```
## 🔧 故障排除
### 常见问题及解决方案
| 问题现象 | 可能原因                                   | 解决方案                       |
|--------|----------------------------------------|----------------------------|
| **❌API Key无效** | 1. Key输入错误 <br> 2. Key未激活 <br> 3. 余额不足 | 1. 检查Key是否正确复制 <br> 2. 确认Key状态 <br> 3. 检查账户余额 |
| **⚠️ 生成失败** |1. 网络连接问题 <br> 2. API服务异常 <br> 3. 需求描述不清晰 | 1. 检查网络连接 <br> 2. 稍后重试 <br> 3. 优化需求描述 |
| **🐢 程序无响应** |1. API响应慢 <br> 2. 处理大量数据 |1. 耐心等待（最长可能1-2分钟） <br> 2. 检查网络状况 |

错误信息解读

- **“API调用失败: ...”：** 通常是网络、Key或服务端问题。请根据具体错误信息判断。

- **“无法解析API返回的JSON格式”：** AI没有返回纯JSON。请检查并强化 system_prompt 中关于“只返回JSON”的指令。

- **“响应内容为空”：** API未返回有效内容。请检查需求输入和网络连接。

## 📝 注意事项
### 安全建议
- 🔐 妥善保管API Key - 不要将Key提交到版本控制系统

- 📁 定期备份 - 建议定期备份生成的测试用例文件

- 🔄 更新维护 - 关注Deepseek API的更新和变更

### 💡 提示：使用过程中如有任何问题或建议，欢迎反馈！
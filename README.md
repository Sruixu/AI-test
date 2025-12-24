# Deepseek 测试用例生成工具

基于Deepseek API的测试用例生成工具，提供图形化界面，可以方便地将需求转换为测试用例并导出为Excel格式。

**参考项目**：[monkey410/Ai-test](https://github.com/monkey410/Ai-test.git)

---

## ✨ 功能特点

- 🖥️ **图形化界面** - 直观易用的桌面应用程序
- ⚙️ **自定义API配置** - 灵活配置Deepseek API参数
- 📝 **模板自定义** - 可修改提示模板以适应不同测试需求
- 📊 **Excel导出** - 生成格式规范的测试用例Excel文件
- 📈 **实时进度显示** - 生成过程可视化反馈
- 🛡️ **错误处理** - 完善的错误提示和异常处理机制

---

## 🚀 快速开始

### 环境要求
- Python 3.10 或更高版本
- 有效的Deepseek API Key

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
   - 访问 [Deepseek控制台](https://platform.deepseek.com/api_keys)
   - 创建并复制您的API Key

4. **启动应用**
   ```bash
   python main_launcher.py
   ```

---

## 📖 使用指南

### 第一步：API设置
在 “config.json”文件配置API_key
   ```bash
     "api": {
    "api_key": "",   在""里输入你的API_key 
    "base_url": "https://api.deepseek.com/v1",
    "models": ["deepseek-reasoner", "deepseek-chat", "qwen-plus"],
    "default_model": "deepseek-reasoner"
  },
   ```

### 第二步：输入需求
运行后在"需求内容"标签页中：
- 粘贴或输入详细的需求描述
- 建议包含功能点、业务场景等关键信息

### 第三步：输出设置
在"输出设置"标签页中：
1. **选择保存路径** - 指定Excel文件存储位置
2. **配置输出选项**：
   - ✅ 包含用例ID
   - ✅ 包含优先级
   - ✅ 包含前置条件


### 第四步：生成测试用例
1. 点击 **"生成测试用例"** 按钮
2. 等待进度条完成（通常需要1分钟多甚至更久，AI在思考。。）
3. 生成完成后会显示保存路径提示

---

## ⚙️ 配置说明

项目使用 `config.json` 配置文件，主要包含：
```json
{
   "api": {
      "api_key": "",
      "base_url": "https://api.deepseek.com/v1",
      "models": [
         "deepseek-reasoner",
         "deepseek-chat",
         "qwen-plus"
      ],
      "default_model": "deepseek-reasoner"
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

- "网络连接失败" - 检查代理设置或网络连接

- "API响应超时" - 尝试减少单次生成的数据量

- "格式解析错误" - 检查需求描述是否包含特殊字符

## 📝 注意事项
### 安全建议
- 🔐 妥善保管API Key - 不要将Key提交到版本控制系统

- 📁 定期备份 - 建议定期备份生成的测试用例文件

- 🔄 更新维护 - 关注Deepseek API的更新和变更

### 💡 提示：使用过程中如有任何问题或建议，欢迎反馈！
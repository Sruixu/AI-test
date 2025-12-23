# Deepseek 测试用例生成工具

基于Deepseek API的测试用例生成工具，提供图形界面，可以方便地将需求转换为测试用例并导出为Excel格式。 

**参考自**：https://github.com/monkey410/Ai-test.git

## 功能特点

- 图形化界面操作
- 支持自定义API配置
- 可自定义提示模板
- Excel格式导出
- 实时进度显示
- 错误提示和处理

## 配置步骤

注意要求：python 3.10以上版本

```
1.克隆项目
pip clone https://github.com/Sruixu/AI-test.git
cd AI-test

2.安装依赖
pip install -r requirements.txt

3.启动main_launcher

```

## 使用步骤

注意要求：先去deepseek 创建API key 网址：https://platform.deepseek.com/api_keys 

1. 启动程序后，在"API设置"标签页：
   - 输入API Key，Base URL，模型
   - System提示的内容可默认不修改
   - 补充中默认可不填

2. 在"需求内容"标签页：
   - 输入需求描述文本

3. 在"输出设置"标签页：
   - 选择Excel文件保存位置
   - 配置输出选项（用例ID、优先级等）

4. 点击"生成测试用例"按钮

5. 等待生成完成，查看生成的Excel文件

## 配置说明

配置文件`config.json`包含以下设置：
- API配置（base_url、模型选项）
- 默认提示模板
- 输出格式设置
- 界面配置

## 常见问题

1. API Key无效
   - 检查API Key是否正确输入
   - 确认API Key是否已激活

2. 生成失败
   - 检查网络连接
   - 确认API服务是否可用
   - 查看错误提示信息

3. 程序无响应
   - 等待API响应（可能需要几秒钟）
   - 检查网络状态

## 注意事项

- 请妥善保管API Key
- 建议定期备份生成的测试用例
- 如遇问题，查看程序提供的错误提示
- 依赖都下载后，只需启动direct_launcher.py文件就行






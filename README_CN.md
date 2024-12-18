# SChat

SChat 是一个强大而灵活的聊天库，为多个 LLM 提供商提供统一的接口。

## 主要特性

- 🚀 **统一接口**: 为多个 LLM 提供商(OpenAI、Anthropic、Google、DeepSeek 等)提供一致的 API
- 🔄 **便捷切换**: 在同一个聊天会话中无缝切换不同的模型
- 🛠️ **丰富功能**:
  - 多模态聊天(文本 + 图像)
  - 函数调用 / 工具使用
  - 流式响应
  - 聊天历史管理
  - 系统提示词
- 🔑 **智能密钥管理**: 自动 API 密钥轮换和负载均衡
- 💾 **会话管理**: 保存和加载聊天会话
- 🔌 **可扩展**: 轻松添加新的提供商

## 安装

```bash
pip install schat
```

## 快速开始

### 基础聊天

```python
from schat import ChatSession

# 创建 OpenAI 会话
session = ChatSession("openai:gpt-4o")

# 发送消息
response = session.send("什么是Python？")
print(response.text)

# 多轮对话
response = session.send("它有哪些主要特点？")
print(response.text)

# 切换到其他模型
response = session.send("告诉我更多", model="anthropic:claude-3-5-haiku-20241022")
print(response.text)
```

### 多模态聊天

```python
# 图片聊天
response = session.send(
    "这张图片里有什么？",
    files=["path/to/image.jpg"]
)
print(response.text)

# 同时使用本地和在线图片
response = session.send(
    "比较这些图片：",
    files=[
        "local_image.jpg",
        "https://example.com/online_image.jpg"
    ]
)
```

### 函数调用

```python
# 定义天气查询工具
weather_tool = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "获取天气信息",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string"},
                "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
            },
            "required": ["location"]
        }
    }
}

# 发送带工具的请求
response = session.send(
    "北京的天气怎么样？",
    tools=[weather_tool]
)

# 处理工具调用
if response.tool_calls:
    for tool_call in response.tool_calls:
        if tool_call["function"]["name"] == "get_weather":
            # 模拟工具返回结果
            result = {
                "location": "北京",
                "temperature": 20,
                "unit": "celsius",
                "condition": "晴天"
            }
            session.add_tool_message(result, tool_call["id"])
    
    # 获取最终响应
    final_response = session.send("继续告诉我天气信息")
    print(final_response.text)
```

### 流式响应

```python
# 启用流式输出
for chunk in session.send("讲个故事", stream=True):
    print(chunk, end="", flush=True)
```

### 会话管理

```python
# 设置系统提示词
session.set_system_prompt("你是一个总是用古文说话的助手。")

# 保存聊天历史
session.save("chat_history.json")

# 加载聊天历史
new_session = ChatSession()
new_session.load("chat_history.json")
```

### API 密钥管理

```python
import os

# 多个密钥用于负载均衡
os.environ["OPENAI_KEY"] = "key1,key2,key3"
os.environ["ANTHROPIC_KEY"] = "key1,key2"
os.environ["GOOGLE_KEY"] = "key1"

# 或直接设置密钥
from schat.models.openai import OpenAIModel
model = OpenAIModel()
model.set_api_key("your-api-key")
```

## 支持的提供商

- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude-3)
- Google (Gemini)
- DeepSeek
- OpenRouter
- GLM (智谱 ChatGLM)
- Qwen (通义千问)
- 更多即将支持...

## 贡献

欢迎提交 Pull Request 来帮助改进这个项目！

## 许可证

本项目采用 MIT 许可证。
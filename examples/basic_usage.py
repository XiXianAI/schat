from schat import ChatSession
from schat.models.openai import OpenAIModel
from schat.models.anthropic import AnthropicModel
import key_env

# 创建模型实例
openai_model = OpenAIModel()
openai_model.set_model_config({"model": "gpt-4"})

anthropic_model = AnthropicModel()
anthropic_model.set_model_config({"model": "claude-3"})

# 创建会话
session = ChatSession(default_model=openai_model)

# 发送普通消息
response = session.send("What's the weather like today?")
print(response.text)

# 发送带图片的消息
response = session.send(
    "What's in this image?",
    files=["path/to/image.jpg"]
)
print(response.text)

# 切换到不同的模型
session.set_model(anthropic_model)
response = session.send("Explain quantum computing")
print(response.text)

# 保存会话
session.save("chat_history.json") 
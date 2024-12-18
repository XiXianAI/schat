from schat import ChatSession, ModelFactory
import os
import key_env

# 使用OpenAI
#session = ChatSession("openai:gpt-4o")
#res = session.send("who are you?")
#print(res.text)

# 使用DeepSeek (会使用DEEPSEEK_KEY)
session = ChatSession("openrouter:qwen/qwen-2.5-coder-32b-instruct")
res = session.send("你是谁?我是小明")
print(res.text)
res = session.send("我是谁?")

print(res.text)

res = session.send("你现在又是谁",model="deepseek:deepseek-chat")
print(res.text)

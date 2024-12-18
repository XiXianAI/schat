import os
from schat import ChatSession
from schat.models.openai import OpenAIModel
from schat.core.message import Message
import key_env

def verify_response(response, expected_type=str, min_length=10):
    """验证响应的基本属性"""
    assert response.role == "assistant"
    assert isinstance(response.text, expected_type)
    assert len(response.text) >= min_length
    print(f"Response: {response.text}\n")

def test_basic_chat():
    """测试基本对话功能"""
    print("\n=== 测试基本对话 ===")
    model = OpenAIModel()
    model.set_model_config({"model": "gpt-4o-mini"})  # 设置默认模型
    session = ChatSession(model)
    
    # 单轮对话
    response = session.send("What is Python?")
    verify_response(response)
    
    # 多轮对话
    response = session.send("What are its main features?")
    verify_response(response)
    
    # 设置system prompt
    session.set_system_prompt("You are a Python expert who always provides code examples.")
    response = session.send("How to read a file in Python?")
    verify_response(response)
    assert "open(" in response.text

def test_streaming():
    """测试流式输出"""
    print("\n=== 测试流式输出 ===")
    model = OpenAIModel()
    model.set_model_config({"model": "gpt-4o"})
    session = ChatSession(model)
    
    print("Streaming response:")
    for chunk in session.send("Tell me a short story.", stream=True):
        print(chunk, end="", flush=True)
    print("\n")

def test_vision():
    """测试图像理解功能"""
    print("\n=== 测试图像理解 ===")
    model = OpenAIModel()
    model.set_model_config({"model": "gpt-4o-mini"})
    session = ChatSession(model)
    
    # 使用本地图片
    response = session.send(
        "What's in this image?",
        files=["examples/test.jpeg"]
    )
    verify_response(response)
    
    # 使用网络图片
    response = session.send(
        "Describe this image:",
        files=["https://python.org/static/img/python-logo.png"]
    )
    verify_response(response)

def test_tools():
    """测试函数调用功能"""
    print("\n=== 测试函数调用 ===")
    model = OpenAIModel()
    model.set_model_config({"model": "gpt-4o"})
    session = ChatSession(model)
    
    # 定义天气查询工具
    weather_tool = {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current weather in a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and state, e.g. San Francisco, CA"
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["c", "f"],
                        "description": "Temperature unit (Celsius or Fahrenheit)"
                    }
                },
                "required": ["location", "unit"]
            }
        }
    }
    
    # 发送初始请求
    response = session.send(
        "What's the weather like in Beijing?",
        tools=[weather_tool]
    )
    print("Assistant:", response.text)
    
    # 如果助手调用了工具
    if response.tool_calls:
        for tool_call in response.tool_calls:
            if tool_call["function"]["name"] == "get_weather":
                # 模拟工具调用结果
                result = {
                    "location": "Beijing",
                    "temperature": 20,
                    "unit": "c",
                    "condition": "sunny"
                }
                
                # 添加工具响应到会话
                session.add_tool_message(result, tool_call["id"])
        
        # 获取最终响应
        final_response = session.send("Continue with the weather information")
        print("Final response:", final_response.text)

def test_key_management():
    """测试API密钥管理"""
    print("\n=== 测试密钥管理 ===")
    
    # 设置环境变量
    os.environ["OPENAI_KEY"] = "key1,key2,key3"
    
    # 创建模型并测试key管理
    model = OpenAIModel()
    model.set_model_config({"model": "gpt-4o-mini"})
    
    # 测试自动从环境变量获取key
    response = model.send([Message(role="user", text="Hello")])
    verify_response(response)
    
    # 测试显式设置key
    model.set_api_key("explicit-key")
    response = model.send([Message(role="user", text="Hello")])
    verify_response(response)
    
    print("Key management test passed")

def test_session_management():
    """测试会话管理"""
    print("\n=== 测试会话管理 ===")
    model = OpenAIModel()
    model.set_model_config({"model": "gpt-4o-mini"})
    session = ChatSession(model)
    
    # 添加一些消息
    session.send("Hello!")
    session.send("What's your name?")
    
    # 保存会话
    session.save("chat_history.json")
    
    # 加载会话
    new_session = ChatSession()
    new_session.load("chat_history.json")
    
    # 验证历史记录
    assert len(new_session.history) == 4  # 2问2答
    print(f"Successfully loaded {len(new_session.history)} messages")
    
    # 清理
    os.remove("chat_history.json")

def main():
    """运行所有测试"""
   
    
    try:
        #test_basic_chat()
        #test_streaming()
        #test_vision()
        test_tools()
        test_key_management()
        test_session_management()
        print("\n所有测试完成!")
        
    except Exception as e:
        print(f"\n测试失败: {str(e)}")
        raise

if __name__ == "__main__":
    main() 
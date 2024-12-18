import os
import json
from schat import ChatSession
import key_env

def test_basic_chat():
    """测试基本对话"""
    print("\n=== 测试基本对话 ===")
    session = ChatSession("anthropic:claude-3-5-haiku-20241022")
    
    # 发送消息
    response = session.send("我是小明，你是谁")
    print("Assistant:", response.text)
    # 多轮对话
    response = session.send("我是谁?")
    print("Assistant:", response.text)

def test_vision():
    """测试图像理解"""
    print("\n=== 测试图像理解 ===")
    session = ChatSession("anthropic")
    
    # 使用本地图片
    response = session.send(
        "这张图片里有什么?",
        files=["examples/test.jpeg"]
    )
    print("Assistant:", response.text)

    response = session.send(
        "这张图片里哪些文字?"
    )
    print("Assistant:", response.text)

    # 使用网络图片
    response = session.send(
        "描述这张图片:",
        files=["https://www.baidu.com/img/PCtm_d9c8750bed0b3c7d089fa7d55720d6cf.png"]
    )
    print("Assistant:", response.text)

def test_function_calling():
    """测试函数调用"""
    print("\n=== 测试函数调用 ===")
    session = ChatSession("anthropic")
    
    # 定义天气查询工具
    weather_tool = {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current weather",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City name"
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "Temperature unit"
                    }
                },
                "required": ["location"]
            }
        }
    }
    
    try:
        # 发送初始请求
        response = session.send(
            "What's the weather like in Beijing? Please provide the temperature in Celsius.",
            tools=[weather_tool]
        )
        print("Assistant:", response.text)
        
        # 如果助手调用了工具
        if response.tool_calls:
            for tool_call in response.tool_calls:
                if tool_call["function"]["name"] == "get_weather":
                    # 解析函数参数
                    args = json.loads(tool_call["function"]["arguments"])
                    
                    # 模拟工具调用结果
                    result = {
                        "location": args["location"],
                        "temperature": 20,
                        "unit": args.get("unit", "celsius"),
                        "condition": "sunny"
                    }
                    
                    # 添加工具响应到会话
                    session.add_tool_message(json.dumps(result), tool_call["id"])
            
            # 获取最终响应
            final_response = session.send("Continue with the weather information")
            print("Final response:", final_response.text)
    
    except Exception as e:
        print(f"Error during function call: {e}")
        import traceback
        traceback.print_exc()

def main():
    try:
        test_function_calling()
        test_vision()
        test_basic_chat()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 
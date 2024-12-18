import os
import traceback
import json
from schat import ChatSession
import key_env


def test_function_calling():
    """测试函数调用功能"""
    print("\n=== 测试函数调用 ===")
    
    session = ChatSession("google:gemini-1.5-pro")
    
    # 定义一个简单的天气查询工具
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
        
        # 如果助手���用了工具
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
        traceback.print_exc()

if __name__ == "__main__":
    try:
        test_function_calling()
    except Exception as e:
        traceback.print_exc()
        print(f"发生错误: {e}")
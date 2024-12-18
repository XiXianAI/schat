import json
import os
from schat import ChatSession
from schat.models.openai import OpenAIModel
import key_env

def get_weather(location: str, unit: str = "c") -> dict:
    """模拟天气查询功能"""
    return {
        "location": location,
        "temperature": 20 if unit == "c" else 68,
        "unit": unit,
        "condition": "sunny"
    }

def main():
    
    
    # 创建会话
    model = OpenAIModel()
    session = ChatSession(model)
    
    # 设置系统提示
    session.set_system_prompt(
        "You are a helpful customer support assistant. Use the supplied tools to assist the user."
    )
    
    # 定义工具
    delivery_tool = {
        "type": "function",
        "function": {
            "name": "get_delivery_date",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string"}
                },
                "required": ["order_id"]
            }
        }
    }
    
    # 发送初始请求
    response = session.send(
        "Hi, can you tell me the delivery date for my order? order_12345",
        tools=[delivery_tool]
    )
    print("Assistant:", response.text)
    
    # 如果助手调用了工具
    if response.tool_calls:
        for tool_call in response.tool_calls:
            if tool_call["function"]["name"] == "get_delivery_date":
                # 模拟工具调用结果
                result = {
                    "order_id": "order_12345",
                    "delivery_date": "2024-03-20 14:30:00"
                }
                
                # 添加工具响应到会话
                session.add_tool_message(result, tool_call["id"])
        
        # 获取最终响应
        final_response = session.send("Continue with the delivery information")
        print("Assistant:", final_response.text)

if __name__ == "__main__":
    main() 


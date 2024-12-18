import pytest
from schat.core.tool import Tool

def test_tool_creation():
    tool = Tool(
        name="weather",
        description="Get weather information",
        parameters={
            "location": {"type": "string", "description": "City name"},
            "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
        },
        required=["location"]
    )
    assert tool.name == "weather"
    assert "location" in tool.required
    assert "unit" in tool.parameters

def test_tool_to_dict():
    tool = Tool(
        name="calculator",
        description="Basic calculator",
        parameters={
            "expression": {"type": "string"},
            "precision": {"type": "integer", "default": 2}
        }
    )
    data = tool.to_dict()
    assert data["name"] == "calculator"
    assert "expression" in data["parameters"]
    assert data["required"] is None

def test_tool_without_required():
    tool = Tool(
        name="echo",
        description="Echo the input",
        parameters={"text": {"type": "string"}}
    )
    assert tool.required is None
    
def test_tool_with_empty_parameters():
    tool = Tool(
        name="ping",
        description="Simple ping",
        parameters={}
    )
    assert tool.parameters == {} 
# SChat

SChat is a powerful and flexible chat library that provides a unified interface for multiple LLM providers.

## Key Features

- 🚀 **Unified Interface**: One consistent API for multiple LLM providers (OpenAI, Anthropic, Google, DeepSeek, etc.)
- 🔄 **Easy Provider Switching**: Seamlessly switch between different models in the same chat session
- 🛠️ **Rich Features Support**:
  - Multi-modal chat (text + images)
  - Function calling / Tools
  - Streaming responses
  - Chat history management
  - System prompts
- 🔑 **Smart Key Management**: Automatic API key rotation and load balancing
- 💾 **Session Management**: Save and load chat sessions
- 🔌 **Extensible**: Easy to add new providers

## Installation

```bash
pip install schat
```

## Quick Start

### Basic Chat

```python
from schat import ChatSession

# Create a session with OpenAI
session = ChatSession("openai:gpt-4o")

# Send a message
response = session.send("What is Python?")
print(response.text)

# Multi-turn conversation
response = session.send("What are its main features?")
print(response.text)

# Switch to a different model
response = session.send("Tell me more", model="anthropic:claude-3-5-haiku-20241022")
print(response.text)
```

### Multi-modal Chat

```python
# Chat with images
response = session.send(
    "What's in this image?",
    files=["path/to/image.jpg"]
)
print(response.text)

# Use both local and online images
response = session.send(
    "Compare these images:",
    files=[
        "local_image.jpg",
        "https://example.com/online_image.jpg"
    ]
)
```

### Function Calling

```python
# Define a weather tool
weather_tool = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get weather information",
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

# Send request with tool
response = session.send(
    "What's the weather in Beijing?",
    tools=[weather_tool]
)

# Handle tool calls
if response.tool_calls:
    for tool_call in response.tool_calls:
        if tool_call["function"]["name"] == "get_weather":
            # Mock tool response
            result = {
                "location": "Beijing",
                "temperature": 20,
                "unit": "celsius",
                "condition": "sunny"
            }
            session.add_tool_message(result, tool_call["id"])
    
    # Get final response
    final_response = session.send("Continue with the weather information")
    print(final_response.text)
```

### Streaming Response

```python
# Enable streaming
for chunk in session.send("Tell me a story", stream=True):
    print(chunk, end="", flush=True)
```

### Session Management

```python
# Set system prompt
session.set_system_prompt("You are a helpful assistant who speaks like Shakespeare.")

# Save chat history
session.save("chat_history.json")

# Load chat history
new_session = ChatSession()
new_session.load("chat_history.json")
```

### API Key Management

```python
import os

# Multiple keys for load balancing
os.environ["OPENAI_KEY"] = "key1,key2,key3"
os.environ["ANTHROPIC_KEY"] = "key1,key2"
os.environ["GOOGLE_KEY"] = "key1"

# Or set key directly
from schat.models.openai import OpenAIModel
model = OpenAIModel()
model.set_api_key("your-api-key")
```

## Supported Providers

- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude-3)
- Google (Gemini)
- DeepSeek
- OpenRouter
- GLM (ChatGLM)
- Qwen (通义千问)
- More coming soon...

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.
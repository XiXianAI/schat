from schat import ChatSession
import key_env

def test_openrouter():
    # 使用Claude模型
    session = ChatSession("openrouter:anthropic/claude-3-5-haiku-20241022")
    response = session.send("Hello, who are you?")
    print(response.text)
    
    # 使用其他模型
    session = ChatSession("openrouter:openai/gpt-4o")
    response = session.send("Hello!")
    print(response.text)

def test_openrouter_with_image():
    session = ChatSession("openrouter:anthropic/claude-3.5-sonnet")
    response = session.send(
        "What's in this image?",
        files=["examples/test.jpeg"]
    )
    print(response.text)

if __name__ == "__main__":
    test_openrouter_with_image() 
    test_openrouter()
    
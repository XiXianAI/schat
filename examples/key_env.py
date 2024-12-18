import os

try:
    import key_env_private
except:
    # 设置代理
    proxy = "http://user:passwd@1.1.1.1:2222"
    #os.environ["http_proxy"] = proxy
    #os.environ["https_proxy"] = proxy
    # 设置API密钥
    os.environ["ANTHROPIC_KEY"] = "your_anthropic_api_key"
    # 设置API密钥
    os.environ["GOOGLE_KEY"] = "your_google_api_key1,your_google_api_key2"
    os.environ["OPENAI_KEY"] = "your_openai_api_key1,your_openai_api_key2"
    os.environ["DEEPSEEK_KEY"] = "your_deepseek_api_key"
    os.environ["OPENROUTER_KEY"] = "your_openrouter_api_key"
    # 设置API密钥
    os.environ["OPENAI_KEY"] = "your_openai_api_key"
    

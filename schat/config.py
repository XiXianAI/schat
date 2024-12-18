"""全局配置"""

# 默认的provider配置
DEFAULT_PROVIDERS = {
    # OpenAI 及其兼容实现
    "openai": {
        "class": "OpenAIModel",
        "base_url": None,
        "default_params": {
            "temperature": 0.7,
            "max_tokens": 8192,
            "model": "gpt-4o-mini"
        }
    },
    "glm": {
        "class": "OpenAIModel",
        "base_url": "https://open.bigmodel.cn/api/paas/v4/chat/completions", 
        "openai_compatible": True,
        "default_params": {
            "temperature": 0.7,
            "max_tokens": 4095
        }
    },
    "qwen": {
        "class": "OpenAIModel",
        "base_url": "https://dashscope-intl.aliyuncs.com/compatible-mode/v1", 
        "openai_compatible": True,
        "default_params": {
            "temperature": 0.7,
            "max_tokens": 4095
        }
    },  
    # Anthropic
    "anthropic": {
        "class": "AnthropicModel",
        "base_url": None,
        "default_params": {
            "temperature": 0.7,
            "max_tokens": 4096,
            "model": "claude-3-5-haiku-20241022"
        }
    },
    
    # DeepSeek
    "deepseek": {
        "class": "OpenAIModel",
        "base_url": "https://api.deepseek.com/beta",
        "openai_compatible": True,
        "default_params": {
            "temperature": 0.7,
            "max_tokens": 8192,
            "model": "deepseek-chat"
        }
    },

    # OpenRouter
    "openrouter": {
        "class": "OpenRouterModel",
        "default_params": {
            "temperature": 0.7,
            "max_tokens": 8192,
            "stream": False,
            "model": "anthropic/claude-3-5-haiku-20241022"  # 默认使用Claude模型
        }
    },

    # Google
    "google": {
        "class": "GoogleModel",
        "base_url": None,
        "default_params": {
            "temperature": 0.7,
            "max_tokens": 8192,
            "model": "gemini-1.5-pro"
        }
    },
} 
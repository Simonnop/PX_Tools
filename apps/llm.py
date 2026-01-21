import os

from dotenv import load_dotenv
from openai import OpenAI

# 加载环境变量
load_dotenv()


def _get_openai_client():
    """创建 OpenAI 客户端（阿里云百炼兼容接口）"""
    # 兼容部分环境：如果存在 HTTP(S)_PROXY 等代理变量，OpenAI SDK 可能会走 proxies 参数路径；
    # 而某些旧版依赖会导致报错：Client.__init__() got an unexpected keyword argument 'proxies'
    # 这里做保守处理：在本进程内移除代理变量，避免触发该路径。
    for k in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"):
        os.environ.pop(k, None)
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError("环境变量 DASHSCOPE_API_KEY 未配置")
    client = OpenAI(
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    return client


def ask_llm(question: str, model: str = "qwen-plus", enable_search: bool = True):
    """
    直接向大模型提问，返回原始回答文本。

    参数:
        question: 必填，用户提问文本
        model: 可选，模型名称，默认 "qwen-plus"
        enable_search: 是否开启搜索，默认 True

    返回:
        (success: bool, result: str)
        success 为 True 时，result 为 LLM 原始回答
        success 为 False 时，result 为错误信息
    """
    if not question or not str(question).strip():
        return False, "question 不能为空"

    try:
        client = _get_openai_client()
        extra = {"extra_body": {"enable_search": bool(enable_search)}} if enable_search else {}

        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": question},
            ],
            **extra,
        )

        content = completion.choices[0].message.content
        return True, content

    except Exception as e:
        return False, str(e)

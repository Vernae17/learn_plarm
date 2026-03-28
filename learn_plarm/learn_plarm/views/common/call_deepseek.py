"""调用DeepSeek API的通用函数"""
from flask import flash


def call_deepseek(prompt,system_prompt="你是一个专业的学习助手"):
    from openai import OpenAI

    api_key = "sk-160599960c244a58acb6c531d0dc81e0"
    # 初始化OpenAI客户端
    client = OpenAI(
        # 如果没有配置环境变量，请用阿里云百炼API Key替换：api_key="sk-xxx"
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )

    try:
        response = client.chat.completions.create(
            model="deepseek-v3.2",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            # 通过 extra_body 设置 enable_thinking 开启思考模式
            extra_body={"enable_thinking": True},
            temperature=0.7,
            max_tokens= 2000
        )

        return response.choices[0].message.content
    except Exception as e:
        flash({f"API调用失败：{e}"})
        return None
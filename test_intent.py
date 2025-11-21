#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
快速测试 DashScope 意图识别功能
用法：
1. 设置环境变量（PowerShell）：
   $env:LLM_PROVIDER = "dashscope"
   $env:LLM_MODEL = "qwen-plus"
   $env:DASH_SCOPE_API_KEY = "sk-xxxx"
2. 运行：python test_intent.py
"""

import os
import sys

# 添加 backEnd 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backEnd'))

# 手动加载 .env 文件（如果存在）
def _load_env_file():
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    # 处理行内注释（# 后面的内容）
                    if '#' in line:
                        line = line.split('#')[0].strip()
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        if key and value and key not in os.environ:
                            os.environ[key] = value
        except Exception as e:
            print(f"读取 .env 文件失败: {e}")

_load_env_file()

from src.Interpreter.intent_service import IntentService


def test_intent_service():
    """测试意图识别服务"""
    service = IntentService()
    
    print("=" * 60)
    print("意图识别服务测试")
    print("=" * 60)
    print(f"LLM Provider: {service.provider or '(未配置，将使用原始匹配)'}")
    print(f"Model: {service.model}")
    print(f"API Key: {'已设置' if service.api_key else '未设置'}")
    print(f"启用状态: {'已启用' if service.enabled else '未启用（降级到原始匹配）'}")
    print("=" * 60)
    print()
    
    # 测试用例
    test_cases = [
        "我想查账单",
        "你好",
        "我要投诉",
        "帮我转人工",
        "套餐怎么升级",
        "支付",
        "分期付款",
    ]
    
    for user_input in test_cases:
        print(f"用户输入: {user_input}")
        result = service.match_intent(user_input)
        print(f"  识别结果: {result.get('intent')}")
        print(f"  标准化文本: {result.get('normalized_text')}")
        print(f"  置信度: {result.get('confidence', 0.0):.2f}")
        print()
    
    print("=" * 60)
    if service.enabled:
        print("✓ LLM 意图识别已启用")
        print("  如果看到识别结果与输入不同，说明 LLM 正在工作")
    else:
        print("⚠ LLM 未启用，使用原始字符串匹配")
        print("  请设置环境变量：")
        print("  LLM_PROVIDER=dashscope")
        print("  DASH_SCOPE_API_KEY=sk-xxxx")
    print("=" * 60)


if __name__ == "__main__":
    test_intent_service()


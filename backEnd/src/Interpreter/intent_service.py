import json
import os
from typing import Dict, List

import requests


def _load_env_file():
    """从项目根目录的 .env 文件加载环境变量"""
    env_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env')
    if not os.path.exists(env_path):
        return
    
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
        print(f"[IntentService] 读取 .env 文件失败: {e}")


# 在模块加载时读取 .env
_load_env_file()


class IntentService:
    """
    调用外部 LLM（默认 DashScope）进行意图识别。
    如果未配置 LLM，则退化为原始字符串匹配，不影响现有流程。
    """

    DEFAULT_INTENTS = [
        "账单", "套餐", "人工", "投诉", "支付", "分期", "方案", "主菜单",
        "申请", "升级", "降级", "流量", "继续", "返回"
    ]

    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "").lower()
        self.model = os.getenv("LLM_MODEL", "qwen-plus")
        self.api_key = os.getenv("DASH_SCOPE_API_KEY", "")
        self.intent_options = self._load_intent_options()
        self.endpoint = os.getenv(
            "DASH_SCOPE_ENDPOINT",
            "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
        )
        self.timeout = self._load_timeout()
        self.enabled = self.provider == "dashscope" and bool(self.api_key)

    def match_intent(self, text: str) -> Dict:
        """
        将用户输入映射为统一意图。
        返回结构：{"intent": "...", "normalized_text": "...", "confidence": 0.xx}
        """
        text = (text or "").strip()
        if not text:
            return {"intent": "", "normalized_text": "", "confidence": 0.0}

        if not self.enabled:
            return {"intent": text, "normalized_text": text, "confidence": 0.0}

        try:
            payload = self._build_payload(text)
            headers = self._build_headers()
            response = requests.post(
                self.endpoint,
                headers=headers,
                json=payload,
                timeout=self.timeout,
            )
            if response.status_code != 200:
                error_msg = response.text[:200] if response.text else "无错误信息"
                print(f"[IntentService] DashScope 调用失败 (状态码 {response.status_code}): {error_msg}")
                return {"intent": text, "normalized_text": text, "confidence": 0.0}

            response_data = response.json()
            llm_text = self._extract_text(response_data)
            parsed = self._parse_json(llm_text)
            if parsed.get("intent"):
                return {
                    "intent": parsed.get("intent", "").strip(),
                    "normalized_text": parsed.get("normalized_text", text).strip(),
                    "confidence": parsed.get("confidence", 0.0),
                }
        except requests.exceptions.RequestException as exc:
            print(f"[IntentService] 网络请求异常: {exc}")
        except json.JSONDecodeError as exc:
            print(f"[IntentService] JSON 解析异常: {exc}")
        except Exception as exc:
            print(f"[IntentService] 意图识别异常: {type(exc).__name__}: {exc}")

        return {"intent": text, "normalized_text": text, "confidence": 0.0}

    # ---------- 内部方法 ----------

    def _build_payload(self, user_text: str) -> Dict:
        options = ", ".join(self.intent_options)
        system_prompt = (
            "你是一个中文客服意图分类器。"
            "只能从候选列表中挑选最合适的意图，并返回 JSON。"
            "JSON 格式固定为："
            '{"intent": "候选意图之一", "normalized_text": "重写后的关键信息", "confidence": 0.0-1.0}\n'
            "如果无法判断，请将 intent 设置为原始输入。"
            f"候选意图列表：[{options}]"
        )
        # DashScope API 格式
        return {
            "model": self.model,
            "input": {
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": f"用户原话：{user_text}\n请只返回 JSON：",
                    },
                ]
            },
            "parameters": {
                "temperature": 0.1,
                "max_tokens": 200,
            }
        }

    def _build_headers(self) -> Dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _extract_text(self, response_json: Dict) -> str:
        output = response_json.get("output", {})
        if isinstance(output, dict):
            if "text" in output and isinstance(output["text"], str):
                return output["text"]
            choices = output.get("choices")
            if choices:
                choice = choices[0]
                message = choice.get("message", {})
                content = message.get("content")
                if isinstance(content, list):
                    return "".join(part.get("text", "") for part in content)
                if isinstance(content, str):
                    return content
        return ""

    def _parse_json(self, text: str) -> Dict:
        snippet = text.strip()
        start = snippet.find("{")
        end = snippet.rfind("}")
        if start != -1 and end != -1 and end > start:
            snippet = snippet[start : end + 1]
        try:
            return json.loads(snippet)
        except json.JSONDecodeError:
            return {}

    def _load_intent_options(self) -> List[str]:
        custom = os.getenv("LLM_INTENT_OPTIONS")
        if custom:
            options = [opt.strip() for opt in custom.split(",") if opt.strip()]
            if options:
                return options
        return self.DEFAULT_INTENTS

    def _load_timeout(self) -> float:
        try:
            return float(os.getenv("LLM_REQUEST_TIMEOUT", "8"))
        except ValueError:
            return 8.0


# DSL 项目

## LLM 意图识别配置（DashScope）
解释器默认仍可基于用户原文匹配分支。如果希望启用通义千问进行意图识别，请设置如下环境变量：

```
LLM_PROVIDER=dashscope
LLM_MODEL=qwen-plus            # 或其他 DashScope 可用模型
DASH_SCOPE_API_KEY=sk-xxxxxxxx # 在 DashScope 控制台生成
# 可选
LLM_INTENT_OPTIONS=账单,套餐,人工,投诉
LLM_REQUEST_TIMEOUT=8
```

配置完成后重新启动后端，即可通过 LLM 对 `Listen` 捕获的自然语言进行标准化，辅助 DSL Branch 命中更智能的意图。

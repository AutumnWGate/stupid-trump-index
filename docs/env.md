统一使用python OpenAI SDK
**应当考虑到不同模型对内容模态的限制**

通义千问
    docs:https://bailian.console.aliyun.com/?tab=api#/api/?type=model&url=https%3A%2F%2Fhelp.aliyun.com%2Fdocument_detail%2F2712576.html&renderType=iframe
    qwen_api_key:sk-5e5b7e6232134b9881a23fc8389fde45
    base_url：https://dashscope.aliyuncs.com/compatible-mode/v1
    model:qwen-vl-max-latest

使用SDK调用时需配置的base_url：https://dashscope.aliyuncs.com/compatible-mode/v1

使用HTTP方式调用时需配置的endpoint：POST https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions


grok
docs:https://docs.x.ai/docs/overview
grok_api_key:xai-54PnifwjOjVYeayYtymUGpJExWkPw95sBzQueovj9I9guCaUhk3f83RaFZznTQtJ7SyO5fjxe2kPKJWW

```python
from openai import OpenAI
    
client = OpenAI(
  api_key=XAI_API_KEY,
  base_url="https://api.x.ai/v1",
)

completion = client.chat.completions.create(
  model="grok-3-beta",
  messages=[
    {"role": "user", "content": "What is the meaning of life?"}
  ]
)
```

gemini
docs:https://ai.google.dev/gemini-api/docs
gemini_api_key:AIzaSyDlEWfLwBunM57SW11HcrkCTpkR248PpJQ
```shell
curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-04-17:generateContent?key=GEMINI_API_KEY" \
-H 'Content-Type: application/json' \
-X POST \
-d '{
  "contents": [{
    "parts":[{"text": "Explain how AI works"}]
    }]
   }'
```





curl --location --request POST 'http://10.51.30.249:8080/v1/chat/completions' \
--header 'User-Agent: Apifox/1.0.0 (https://apifox.com)' \
--header 'Content-Type: application/json' \
--header 'Authorization: Bearer tLJURLIcLm3OvU7xgG2T85ZgMvVuOWoWtaxa3uKMNEU0lAUkBRo6Y7PXymcGi9ha' \
--data-raw '{
  "model": "ai-search",
  "messages": [
    {
      "role": "user",
      "content": "预测一下黄金价格走势"
    }
  ],
  "stream": true,
  "request_id": "818080b4ed5b47f5bfaa4392a4f7844f",
  "temperature": 0.95,
  "top_p": 0.7,
  "seed": 42,
  "max_tokens": 4096,
  "tools": [
    {
      "type": "simple_browser",
      "simple_browser": {
        "browser": ""
      }
    },
    {
      "type": "function",
      "function": {
        "name": "黄金价格",
        "description": "插件功能：该工具专用于查询国内黄金的价格信息。当用户输入明确的实时黄金价格需求时，请调用工具进行查询",
        "parameters": {
          "properties": {},
          "required": [],
          "type": "object"
        }
      }
    },
    {
      "type": "code_interpreter",
      "code_interpreter": {
        "tool_state": {}
      }
    }
  ],
  "conversation_id": "67f3680aab564ad5891212b9"
}'
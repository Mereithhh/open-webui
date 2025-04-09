## R1 协议


### 请求 curl 
其中，认证头是必须有的，模型必须为 deep-research
```
curl --location --request POST 'http://10.51.30.249:8080/v1/chat/completions' \
--header 'Content-Type: application/json' \
--header 'Authorization: Bearer tLJURLIcLm3OvU7xgG2T85ZgMvVuOWoWtaxa3uKMNEU0lAUkBRo6Y7PXymcGi9ha' \
--data-raw '{
  "model": "deep-research",
  "messages": [
    {
      "role": "user",
      "content": "帮我查一下月之暗面创始人本科导师创办的公司叫什么"
    }
  ],
  "stream": true,
  "temperature": 0.95,
  "top_p": 0.7,
  "seed": 42,
  "max_tokens": 4096
}'
```

## 响应
为 sse 流式响应
```

```
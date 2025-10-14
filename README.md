# TradeTheNews

You can start the news scorer container with:

```bash
docker run --rm \
  -e LLM_URL="${LLM_URL}" \
  -e LLM_TOKEN="${LLM_TOKEN}" \
  -p 127.0.0.1:1001:9720 \
  org.ttlab/llm-impact-scorer:0.1
```


```bash
docker run --rm \
  -p 127.0.0.1:1000:9714 \
  org.ttlab/embeddings:latest
```

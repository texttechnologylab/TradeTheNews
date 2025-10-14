import os
import re
import json
import unicodedata
from typing import Tuple

import requests
from fastapi import FastAPI, Response
from fastapi.responses import PlainTextResponse, JSONResponse
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel

LLM_URL = os.getenv("LLM_URL")
LLM_TOKEN = os.getenv("LLM_TOKEN")

class DUUIRequest(BaseModel):
    title: str = ""
    summary: str = ""
    symbol: str = ""

class LLMItem(BaseModel):
    text: str
    score: str
    reason: str
    prompt: str
    raw_json: str

class DUUIResponse(BaseModel):
    items: list[LLMItem]

app = FastAPI(openapi_url="/openapi.json", docs_url="/api", redoc_url=None)

def build_prompt(title: str, summary: str, symbol: str) -> str:
    # try:
    #     with open("/app/prompt.txt", "r") as f:
    #         prompt_t = f.read()
    # except Exception as e:
    #     print(f"Error reading prompt file: {e}")
    #     print("Resorting to default prompt.")
    #     print("Make sure your prompt is mounted on /app/prompt.txt")
    prompt_t = (
    f"You are a financial news analyst. Your task is to judge the likely short-term price impact "
    f"of this news on {symbol} shares over the NEXT 20 MINUTES.\n\n"
    "Return a single valid JSON object with this schema (no markdown fences):\n"
    "{\n"
    '  "score": <integer from -10 to 10>,\n'
    '  "reason": "<one short sentence explaining the main factor driving this impact>"\n'
    "}\n\n"
    "Rules:\n"
    "- Positive values (>0) = bullish (price likely to rise).\n"
    "- Negative values (<0) = bearish (price likely to fall).\n"
    f"- Zero (0) = neutral or unrelated to {symbol}.\n"
    "- Magnitude reflects strength of impact (10 = very strong, 1 = very weak).\n"
    "- OUTPUT MUST BE RAW JSON ONLY. DO NOT use code blocks. DO NOT include commentary.\n"
    "- The score must be a JSON number (no leading '+').\n\n"
    "Examples (valid JSON):\n"
    '  {"score": 7, "reason": "Strong earnings beat is expected to lift demand for shares."}\n'
    '  {"score": -6, "reason": "Legal action increases risk and could pressure the stock."}\n'
    '  {"score": 0,  "reason": "Not related to the company."}\n\n"'
    f"Article Title: {title}\n"
    f"Article Summary: {summary}\n\n"
    "Respond with nothing but the JSON object."
    )
    # prompt = prompt_t.format(title=title, summary=summary, symbol=symbol)
    return prompt_t



def call_api(title: str, summary: str, symbol: str) -> Tuple[str,str,str,str,str]:
    prompt = build_prompt(title, summary, symbol)
    try:
        headers = {'Authorization': f'Bearer {LLM_TOKEN}'}
        resp = requests.post(
            LLM_URL,
            json={'model': 'gemma3:latest', 'messages': [{'role':'user','content':prompt}]},
            headers=headers,
            timeout=30
        )
        resp.raise_for_status()
        content = resp.json()['choices'][0]['message']['content'].strip()
        if content.startswith("```"):
            content = re.sub(r"^```(?:json)?\s*", "", content)
            content = re.sub(r"\s*```$", "", content)
        m = re.search(r"\{.*\}", content, flags=re.DOTALL)
        if not m:
            return "", "0", f"No text could be parsed from LLM", prompt, "{}"
        json_str = m.group(0)
        json_str = re.sub(r'(:\s*)\+(\d+)', r'\1\2', json_str)
        obj = json.loads(json_str)
        score = str(int(obj.get("score", 0)))
        reason = str(obj.get("reason", "")).strip()

        if title:
            text = title.strip()
        else:
            text = ""
        if summary.strip():
            if text:
                text = text + "\n\n" + summary.strip()
            else:
                text = summary.strip()

        return text, score, reason, prompt, json_str
    except Exception as e:
        text = (title + "\n\n" + summary).strip()
        return text, "0", f"Error parsing: {e}", prompt, "{}"

@app.get("/v1/details/input_output")
def get_input_output() -> JSONResponse:
    return {"inputs": ["org.example.LLMAnalysis"], "outputs": ["org.example.LLMAnalysis"]}

with open("dkpro-core-types.xml","rb") as f:
    _typesystem = f.read()

@app.get("/v1/typesystem")
def get_typesystem() -> Response:
    return Response(content=_typesystem, media_type="application/xml")

with open("communication.lua","rb") as f:
    _lua = f.read().decode("utf-8")

@app.get("/v1/communication_layer", response_class=PlainTextResponse)
def get_communication_layer() -> str:
    return _lua

@app.post("/v1/process")
def post_process(req: DUUIRequest) -> DUUIResponse:
    req_title = req.title
    req_summary = req.summary

    clean_title = req_title.encode("utf-16", "surrogatepass").decode("utf-16", "ignore")  # clean
    clean_title = unicodedata.normalize("NFC", clean_title)
    clean_title = re.sub(r"\s+", " ", clean_title).strip()

    clean_summary = req_summary.encode("utf-16", "surrogatepass").decode("utf-16", "ignore")  # clean
    clean_summary = unicodedata.normalize("NFC", clean_summary)
    clean_summary = re.sub(r"\s+", " ", clean_summary).strip()

    text,summary,reason,prompt,json = call_api(clean_title, clean_summary, req.symbol)
    return DUUIResponse(items=[LLMItem(text=text, score=summary, reason=reason ,prompt=prompt, raw_json=json)])

app.openapi_schema = get_openapi(
    title="llm-impact-scorer",
    description="LLMAnalysis for DUUI",
    version="1",
    routes=app.routes
)

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run("app:app", host="0.0.0.0", port=9720, workers=1)

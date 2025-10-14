from typing import List
import os
import numpy as np
from fastapi import FastAPI, Response
from fastapi.responses import PlainTextResponse, JSONResponse
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import re, unicodedata

MODEL_NAME = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
DEVICE = os.getenv("DEVICE_MODEL", "cpu")
model = SentenceTransformer(MODEL_NAME, device=DEVICE)
EMB_DIM = model.get_sentence_embedding_dimension()


class DUUIRequest(BaseModel):
    doc_text: str

class EmbeddingItem(BaseModel):
    iBegin: int
    iEnd: int
    vector: List[float]

class DUUIResponse(BaseModel):
    embeddings: List[EmbeddingItem]


def analyse(doc_text: str) -> List[EmbeddingItem]:
    doc_text = doc_text.strip()
    text = "" if doc_text == "" else doc_text
    if not text:
        zero = np.zeros(EMB_DIM, dtype=np.float32).tolist()
        return [EmbeddingItem(iBegin=0, iEnd=0, vector=zero)]

    sentences_txt = []
    for piece in re.finditer(r'[^.!?]+[.!?]?', text):
        start = piece.start()
        end = piece.end()
        sent = text[start:end]
        sentences_txt.append((start, end, sent))
    if not sentences_txt:
        sentences_txt.append((0, len(text), text))

    sentences = []
    for x, y, sent_txt in sentences_txt:
        clean_sentence_txt = sent_txt.encode("utf-16", "surrogatepass").decode("utf-16", "ignore") # clean
        clean_sentence_txt = unicodedata.normalize("NFC", clean_sentence_txt)
        clean_sentence_txt = re.sub(r"\s+", " ", clean_sentence_txt).strip()
        sentences.append(clean_sentence_txt)


    print("HIHI")
    print(sentences)
    sentence_vecs = model.encode(
        sentences,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    ).astype(np.float32)

    items: List[EmbeddingItem] = []
    for idx in range(len(sentences_txt)):
        start, end, idk = sentences_txt[idx]
        vec = sentence_vecs[idx]
        item = EmbeddingItem(iBegin=start, iEnd=end, vector=vec.tolist())
        items.append(item)

    total_vec = sentence_vecs.mean(axis=0)
    norm = np.linalg.norm(total_vec)
    if norm > 0:
        total_vec = total_vec / norm
    item_doc = EmbeddingItem(iBegin=0, iEnd=len(text), vector=total_vec.tolist())
    items.append(item_doc)

    return items

app = FastAPI(openapi_url="/openapi.json", docs_url="/api", redoc_url=None)

@app.get("/v1/details/input_output")
def get_input_output() -> JSONResponse:
    return {"inputs": [], "outputs": ["org.example.Embede"]}

with open("dkpro-core-types.xml", "rb") as f:
    _typesystem = f.read()

@app.get("/v1/typesystem")
def get_typesystem() -> Response:
    return Response(content=_typesystem, media_type="application/xml")

with open("communication.lua", "rb") as f:
    lua_c = f.read().decode("utf-8")


@app.get("/v1/communication_layer", response_class=PlainTextResponse)
def get_communication_layer() -> str:
    return lua_c

@app.post("/v1/process")
def post_process(request: DUUIRequest) -> DUUIResponse:
    return DUUIResponse(embeddings=analyse(request.doc_text))

openapi_schema = get_openapi(
    title="embeddings-cpu",
    description="CPU embeddings for DUUI",
    version="1",
    routes=app.routes
)
app.openapi_schema = openapi_schema

# import uvicorn
# if __name__ == "__main__":
#     uvicorn.run("sentence_transformers:app", host="0.0.0.0", port=9714, workers=1)
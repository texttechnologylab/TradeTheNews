FROM python:3.12


ARG EMBED_MODEL="sentence-transformers/all-MiniLM-L6-v2"
ARG DEVICE_MODEL="cpu"
ENV EMBED_MODEL=${EMBED_MODEL} \
    DEVICE_MODEL=${DEVICE_MODEL}

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

COPY app.py communication.lua dkpro-core-types.xml ./

RUN python - <<'PY'
import os
from sentence_transformers import SentenceTransformer
model_name = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
device     = os.getenv("DEVICE_MODEL", "cpu")
SentenceTransformer(model_name, device=device)
PY

EXPOSE 9714
CMD ["uvicorn","app:app","--host","0.0.0.0","--port","9714","--workers","1"]

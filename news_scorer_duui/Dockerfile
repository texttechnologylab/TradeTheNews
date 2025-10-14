FROM python:3.12

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

COPY app.py communication.lua dkpro-core-types.xml ./

EXPOSE 9720
CMD ["uvicorn","app:app","--host","0.0.0.0","--port","9720","--workers","1"]

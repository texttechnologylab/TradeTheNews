# TradeTheNews
## Backend
You can start the news scorer container with:

```bash
docker run --rm \
  -e LLM_URL="${LLM_URL}" \
  -e LLM_TOKEN="${LLM_TOKEN}" \
  -p 127.0.0.1:1001:9720 \
  org.ttlab/llm-impact-scorer:0.1
```

..and the embedding container with:
```bash
docker run --rm \
  -p 127.0.0.1:1000:9714 \
  org.ttlab/embeddings:latest
```
 
Compile the Java Application with maven. Run the Main whenever you want to analyze the news inside the Database.
News can be loaded to the Database via the frontend. 
The Java Application is looking in the enviornment for the necessary variables to build the connection string (have a look in org.example.MongoDBHandler.java).

## Frontend
## Setup the Project tradeTheNews

### 1. For the Project you need:

Before starting, make sure you have:

- **Python 3.9+** → [Download](https://www.python.org/downloads/)
- **pip** (included with Python)

Check your installation:
```bash
python --version
pip --version
```

### 2. Furthermore you should do all the Installation in a Virtual Envirement
#### On Windows
```bash
python -m venv_name venv_name
venv_name\Scripts\activate
```
#### On macOS / Linux
```bash
python3 -m venv_name venv_name
source venv_name/bin/activate
```
#### To deactivate:
```bash
deactivate
```

### 3. Installing Dependencies/Requriements
```bash
pip install -r requirements_frontend.txt
```

### 4. Run the Project
```bash
python main.py
```


# Test-Case-Generation-Backend

### Install the Python environment
Install from the [Official Python](https://www.python.org/downloads/)

Check with
```bash
python --version
pip --version
```

### Install ollama
Download ollama from the [Official Ollama](https://ollama.com/download/windows)

Check with
```bash
ollama --version
```

### Install the dependencies
After pulling the code
```bash
cd Test-Case-Generation-Backend
pip install -r requirements.txt
```

### Pulling the ollama model
Pull any model name that your `.env` is using
```bash
ollama pull <model_name>
```
<hr>

# Run the backend
```bash
uvicorn app.main:app --reload
```
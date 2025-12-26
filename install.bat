@echo off
echo Installing Multi-Agent LangGraph Application...
echo.

echo Step 1: Installing Python dependencies...
pip install -r requirements.txt

echo.
echo Step 2: Checking Ollama installation...
ollama --version
if %errorlevel% neq 0 (
    echo Ollama not found! Please install Ollama from https://ollama.ai/
    echo After installing Ollama, run: ollama pull llama2
    pause
    exit /b 1
)

echo.
echo Step 3: Pulling Ollama model (this may take a while)...
ollama pull llama2

echo.
echo Step 4: Testing Ollama connection...
ollama list

echo.
echo Installation complete!
echo.
echo To run the application:
echo   streamlit run app.py
echo.
echo Make sure Ollama is running before starting the application.
pause

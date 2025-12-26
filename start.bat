@echo off
echo Starting Multi-Agent AI Assistant...
echo.

echo Checking Ollama status...
ollama list >nul 2>&1
if %errorlevel% neq 0 (
    echo Starting Ollama service...
    start /B ollama serve
    timeout /t 5 /nobreak >nul
)

echo Starting Streamlit application...
streamlit run app.py

pause

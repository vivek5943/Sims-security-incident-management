@echo off
REM ─────────────────────────────────────────────────────────────────────────
REM SIMS — Setup Script for Windows
REM MCSP-232 | IGNOU MCA-2
REM ─────────────────────────────────────────────────────────────────────────

echo.
echo ══════════════════════════════════════════════════════════════
echo   SIMS — AI-Powered Security Incident Management System
echo   MCSP-232 Project Setup ^| IGNOU MCA-2
echo ══════════════════════════════════════════════════════════════
echo.

cd backend

echo [1/4] Creating Python virtual environment...
python -m venv venv
call venv\Scripts\activate.bat

echo [2/4] Installing Python dependencies...
pip install -r requirements.txt

echo [3/4] Downloading NLTK data...
python -c "import nltk; [nltk.download(p, quiet=True) for p in ['punkt','stopwords','wordnet','omw-1.4']]; print('NLTK ready')"

if not exist .env (
  copy .env.example .env
  echo   .env created — edit DB credentials now!
  pause
)

echo [4/4] Running migrations, seeding data, training ML model...
python manage.py makemigrations authentication incidents ml_engine notifications audit
python manage.py migrate
python manage.py seed_data
python manage.py train_ml_model

cd ..\frontend
echo Installing frontend dependencies...
call npm install

cd ..

echo.
echo ══════════════════════════════════════════════════════════════
echo   SIMS Setup Complete!
echo ══════════════════════════════════════════════════════════════
echo.
echo   Start backend:
echo     cd backend ^&^& venv\Scripts\activate ^&^& python manage.py runserver
echo.
echo   Start frontend (new terminal):
echo     cd frontend ^&^& npm run dev
echo.
echo   Frontend  : http://localhost:5173
echo   Backend   : http://localhost:8000
echo.
echo   admin@sims.local    / Admin@1234
echo   manager@sims.local  / Manager@1234
echo   analyst1@sims.local / Analyst@1234
echo.
pause

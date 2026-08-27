#!/usr/bin/env bash
# SIMS v3 — One-Command Setup (30 security fixes applied across 3 passes)
set -e
G='\033[0;32m' B='\033[0;34m' Y='\033[1;33m' R='\033[0;31m' N='\033[0m'

echo -e "\n${B}══════════════════════════════════════════════════════════════${N}"
echo -e "${B}  SIMS v3 — AI-Powered Security Incident Management System${N}"
echo -e "${B}  MCSP-232 | 3-pass security review | 30 total fixes${N}"
echo -e "${B}══════════════════════════════════════════════════════════════${N}\n"

cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt --quiet

echo -e "${Y}[1/5] Pre-downloading NLTK data (FIX-04 v2)...${N}"
python manage.py download_nltk_data
echo -e "${G}  ✅ NLTK data ready${N}"

if [ ! -f .env ]; then
  cp .env.example .env
  echo -e "${R}  ⚠  .env created — edit SECRET_KEY before continuing!${N}"
  read -p "  Press Enter after editing .env..."
fi

echo -e "${Y}[2/5] Database migrations (includes LoginAttempt model)...${N}"
python manage.py makemigrations authentication incidents ml_engine notifications audit --no-input 2>/dev/null || true
python manage.py migrate --no-input
echo -e "${G}  ✅ Migrations applied${N}"

echo -e "${Y}[3/5] Seeding roles + demo users...${N}"
python manage.py seed_data
echo -e "${G}  ✅ Data seeded${N}"

echo -e "${Y}[4/5] Training ML classifiers (50 samples/category, calibrated)...${N}"
python manage.py train_ml_model
echo -e "${G}  ✅ Calibrated Category + Severity models trained${N}"

cd ../frontend
echo -e "${Y}[5/5] Frontend dependencies...${N}"
[ ! -f .env.local ] && cp .env.example .env.local 2>/dev/null || true
npm install --silent
echo -e "${G}  ✅ Frontend ready${N}"
cd ..

echo ""
echo -e "${G}══════════════════════════════════════════════════════════════${N}"
echo -e "${G}  SIMS v3 Ready — 30 security/quality fixes applied${N}"
echo -e "${G}══════════════════════════════════════════════════════════════${N}"
echo ""
echo -e "  ${Y}Terminal 1 (Backend):${N}"
echo -e "    cd backend && source venv/bin/activate && python manage.py runserver"
echo -e "  ${Y}Terminal 2 (Frontend):${N}"
echo -e "    cd frontend && npm run dev"
echo ""
echo -e "  🌐 Frontend  → http://localhost:5173"
echo -e "  🔌 Backend   → http://localhost:8000/admin/"
echo ""
echo -e "  ${Y}Demo credentials:${N}"
echo -e "    admin@sims.local    / Admin@1234    (System Administrator)"
echo -e "    manager@sims.local  / Manager@1234  (Security Manager)"
echo -e "    analyst1@sims.local / Analyst@1234  (Security Analyst)"
echo ""
echo -e "  ${R}Production checklist:${N} See SECURITY_NOTES.md"
echo -e "  ${R}All fix details:${N}      See V3_DEEP_FIXES.md"
echo ""

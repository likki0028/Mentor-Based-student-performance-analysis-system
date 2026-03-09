#!/usr/bin/env bash
# Render build script for backend
set -o errexit

cd backend
pip install -r requirements.txt

# Initialize database and seed demo data
python init_db.py
python scripts/seed_data.py

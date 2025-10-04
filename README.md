IQ Option OTC 1-Min Bot (Windows 64-bit build ready)

- Designed to run initially in PRACTICE (demo) mode.
- Scans OTC assets, analyses 1-minute candles, and executes 1-minute trades.
- Includes sequential follow-up trades logic: if a trade wins, next trade uses same stake; if it loses, stake increases by RECOVERY_MULTIPLIER to attempt recovery (configurable).
- WARNING: Martingale/recovery strategies increase risk. Use with caution and test extensively in demo.

USAGE (Replit / Cloud):
1. Upload this project to Replit or GitHub.
2. Set environment variables (use .env.example as reference).
3. Install requirements: pip install -r requirements.txt
4. Run: python main.py

BUILD .exe via GitHub Actions (workflow included):
- Push to GitHub main branch. Workflow .github/workflows/build-windows.yml will build dist/main.exe as artifact.

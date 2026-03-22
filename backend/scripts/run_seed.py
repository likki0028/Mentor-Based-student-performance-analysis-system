"""Run the seed script and capture any errors to a log file."""
import sys, os, traceback
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.abspath(__file__)).replace('\\scripts', ''))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from scripts.seed_all_data import seed_all
    seed_all()
except Exception as e:
    with open("seed_error_log.txt", "w", encoding="utf-8") as f:
        f.write(f"Error: {e}\n\n")
        traceback.print_exc(file=f)
    print(f"ERROR written to seed_error_log.txt: {e}")

"""Extract error info from seed_error.log"""
import os
log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "seed_error.log")
with open(log_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Write a simplified version
out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "error_summary.txt")
with open(out_path, "w", encoding="ascii", errors="replace") as out:
    out.write(f"Total lines: {len(lines)}\n")
    for i, line in enumerate(lines):
        line = line.rstrip()
        if any(kw in line.lower() for kw in ["error", "sqlite", "table", "column", "no such"]):
            out.write(f"L{i}: {line}\n")
    out.write("\n--- LAST 5 LINES ---\n")
    for line in lines[-5:]:
        out.write(line.rstrip() + "\n")

print("Written to error_summary.txt")

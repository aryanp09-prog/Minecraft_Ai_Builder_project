# =============================================================
#  setup.py  —  One-click setup for AI Minecraft Builder
#  Run this ONCE before playing:  python setup.py
# =============================================================

import subprocess
import sys
import os

def run(cmd):
    print(f"\n>>> {cmd}")
    result = subprocess.run(cmd, shell=True)
    return result.returncode

print("=" * 55)
print("  AI Minecraft Builder — Setup")
print("=" * 55)

# ── Step 1: Install all required packages ─────────────────────
print("\n[1/3] Installing required packages...")
code = run(f"{sys.executable} -m pip install -r requirements.txt")
if code != 0:
    print("\nERROR: Package installation failed.")
    print("Make sure Python is installed and try again.")
    input("Press Enter to exit...")
    sys.exit(1)
print("Packages installed successfully.")

# ── Step 2: Generate training data ───────────────────────────
print("\n[2/3] Generating AI training data...")
code = run(f"{sys.executable} generate_data.py")
if code != 0:
    print("\nERROR: Could not generate training data.")
    input("Press Enter to exit...")
    sys.exit(1)
print("Training data generated.")

# ── Step 3: Train the AI model ────────────────────────────────
print("\n[3/3] Training the AI model...")
code = run(f"{sys.executable} train_model.py")
if code != 0:
    print("\nERROR: Could not train AI model.")
    input("Press Enter to exit...")
    sys.exit(1)
print("AI model trained and saved.")

# ── Done ──────────────────────────────────────────────────────
print("\n" + "=" * 55)
print("  Setup complete!")
print("  Run the game with:  python main.py")
print("=" * 55)
input("\nPress Enter to launch the game now...")
run(f"{sys.executable} main.py")

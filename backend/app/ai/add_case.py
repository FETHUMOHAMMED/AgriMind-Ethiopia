import os
import csv
from datetime import datetime

CSV_PATH = r"C:\projects\AgriMind-Ethiopia\backend\app\ai\datasets\DATASET_REGISTER_MASTER.csv"

# ============================================================
# FILL IN NEW CASE DETAILS
# ============================================================
CASE_ID = "ETH-0006"
CROP = "Tomato"
DISEASE = "EarlyBlight"
AEZ = "Woina Dega"
REGION = "Oromia"
WOREDA = "Adama"
GPS = "8.54N 39.27E"
ALTITUDE = "1650"
DATE = "2026-12-10"
COLLECTOR = "Agri Expert"
PARTNER = "Melkassa ARC"
EXPERT_ID = "E-006"
LAB_TEST = "Pending"
VERIFICATION = "Tier 2"

# Images folder (already renamed)
FOLDER = rf"C:\projects\AgriMind-Ethiopia\backend\app\ai\datasets\field_images\raw\tomato\early_blight"

# ============================================================

def add_case():
    # Count images in folder
    images = [f for f in os.listdir(FOLDER) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

    if not images:
        print(f"No images in {FOLDER}")
        return

    # Check for duplicate Case_ID
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['Case_ID'] == CASE_ID:
                print(f"Error: {CASE_ID} already exists in the register.")
                return

    # Append new row
    with open(CSV_PATH, 'a', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            CASE_ID, CROP, DISEASE, AEZ, REGION, WOREDA,
            GPS, ALTITUDE, DATE, COLLECTOR, PARTNER,
            EXPERT_ID, LAB_TEST, VERIFICATION
        ])

    print(f"Added {CASE_ID} to register with {len(images)} images.")

if __name__ == "__main__":
    add_case()
import os
import shutil
from datetime import datetime

SOURCE = r"C:\projects\AgriMind-Ethiopia\backend\app\ai\datasets\field_images\raw"
BACKUP_BASE = r"C:\projects\AgriMind-Ethiopia\BACKUPS"

# Create dated backup folder
date_str = datetime.now().strftime("%Y-%m-%d")
backup_folder = os.path.join(BACKUP_BASE, f"field_images_{date_str}")
os.makedirs(backup_folder, exist_ok=True)

# Count files
total = 0
for root, dirs, files in os.walk(SOURCE):
    for file in files:
        if file.lower().endswith(('.jpg', '.jpeg', '.png')):
            total += 1

# Copy
shutil.copytree(SOURCE, backup_folder, dirs_exist_ok=True)
print(f"Backup complete: {total} images copied to {backup_folder}")
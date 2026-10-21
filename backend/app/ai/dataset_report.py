import csv
import os

CSV_PATH = r'C:\projects\AgriMind-Ethiopia\backend\app\ai\datasets\DATASET_REGISTER_MASTER.csv'

def generate_report():
    if not os.path.exists(CSV_PATH):
        print(f"File not found: {CSV_PATH}")
        return

    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print("=" * 60)
    print("AGRIMIND MULTI-MODAL DATASET REPORT")
    print("=" * 60)
    print(f"Total cases: {len(rows)}")
    total_images = sum(int(r.get('Image_Count', 0) or 0) for r in rows)
    print(f"Total images: {total_images}")
    print()

    # Verification levels
    tier1 = sum(1 for r in rows if r.get('Verification_Level') == 'Tier 1')
    tier2 = sum(1 for r in rows if r.get('Verification_Level') == 'Tier 2')
    tier3 = sum(1 for r in rows if r.get('Verification_Level') == 'Tier 3')
    tier4 = sum(1 for r in rows if r.get('Verification_Level') == 'Tier 4')

    print("VERIFICATION LEVELS:")
    print(f"  Tier 1 (unverified):        {tier1}")
    print(f"  Tier 2 (expert-assessed):   {tier2}")
    print(f"  Tier 3 (lab-confirmed):     {tier3}")
    print(f"  Tier 4 (independent eval):  {tier4}")
    print()

    # Environmental data completeness
    has_gps = sum(1 for r in rows if r.get('GPS_Lat') and r.get('GPS_Lon'))
    has_temp = sum(1 for r in rows if r.get('Temp_C'))
    has_humidity = sum(1 for r in rows if r.get('Humidity_Pct'))
    has_rainfall = sum(1 for r in rows if r.get('Rainfall_7d_mm'))
    has_altitude = sum(1 for r in rows if r.get('Altitude_m'))

    print("ENVIRONMENTAL DATA COMPLETENESS:")
    print(f"  GPS coordinates:    {has_gps}/{len(rows)}")
    print(f"  Altitude:           {has_altitude}/{len(rows)}")
    print(f"  Temperature:        {has_temp}/{len(rows)}")
    print(f"  Humidity:           {has_humidity}/{len(rows)}")
    print(f"  Rainfall (7d):      {has_rainfall}/{len(rows)}")
    print()

    # By crop
    crops = {}
    for r in rows:
        crop = r.get('Crop', 'Unknown')
        crops[crop] = crops.get(crop, 0) + 1
    print("BY CROP:")
    for crop, count in sorted(crops.items(), key=lambda x: -x[1]):
        print(f"  {crop}: {count}")
    print()

    # By AEZ
    aezs = {}
    for r in rows:
        aez = r.get('AEZ', 'Unknown')
        aezs[aez] = aezs.get(aez, 0) + 1
    print("BY AGROECOLOGICAL ZONE:")
    for aez, count in sorted(aezs.items(), key=lambda x: -x[1]):
        print(f"  {aez}: {count}")
    print()

    # By partner
    partners = {}
    for r in rows:
        p = r.get('Partner_Institution', 'Unknown')
        partners[p] = partners.get(p, 0) + 1
    print("BY PARTNER INSTITUTION:")
    for p, count in sorted(partners.items(), key=lambda x: -x[1]):
        print(f"  {p}: {count}")
    print()

    # Lab status
    lab_pending = sum(1 for r in rows if r.get('Lab_Test') == 'Pending')
    lab_done = sum(1 for r in rows if r.get('Lab_Test', '').startswith('Completed'))
    print("LAB STATUS:")
    print(f"  Pending:     {lab_pending}")
    print(f"  Completed:   {lab_done}")
    print("=" * 60)

if __name__ == '__main__':
    generate_report()
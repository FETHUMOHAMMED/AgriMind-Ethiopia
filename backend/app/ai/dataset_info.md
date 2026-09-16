# AgriMind Ethiopian Crop Disease Dataset

## Current Status
- Total images: 31
- Source: Google Images (pilot collection)
- Collection date: September 2026
- Validation: NOT yet validated by agricultural experts

## Class Distribution

| Crop | Disease | Images |
|------|---------|--------|
| Coffee | Leaf Rust | 4 |
| Maize | Common Rust | 3 |
| Maize | Northern Leaf Blight | 4 |
| Potato | Early Blight | 3 |
| Potato | Late Blight | 3 |
| Tomato | Early Blight | 4 |
| Tomato | Healthy | 3 |
| Tomato | Late Blight | 4 |
| Wheat | Brown Rust | 3 |

## Limitations
- Small dataset (31 images total)
- Source: Internet images, NOT Ethiopian field data
- Not validated by agricultural experts
- No geographic diversity
- May not represent real Ethiopian field conditions

## Next Steps
1. Collect field images from Ethiopian farms
2. Get expert validation from agricultural institutions
3. Split by location (not randomly) for realistic testing
4. Add metadata (date, location, crop variety, weather)
5. Train CNN (MobileNetV2) instead of Random Forest
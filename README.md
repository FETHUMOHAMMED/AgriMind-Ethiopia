# AgriMind Ethiopia

**AI-powered crop disease detection and farmer assistance platform for Ethiopia.**

AgriMind Ethiopia lets farmers photograph a diseased crop leaf and receive an instant AI diagnosis with treatment recommendations in Amharic, Afaan Oromo, or English.

---

## What This Is

A working end-to-end product — not a mockup. Farmers can register, log in, upload a crop photo, get an AI diagnosis, view prediction history, and switch languages. The system runs as both an Android app and a Flutter web app.

## Features

- User authentication (JWT-based)
- Farmer and Admin roles
- AI crop disease detection (image-based prediction)
- Prediction history tracking
- Image upload and storage
- AI recommendation system
- Multilingual: Amharic, Afaan Oromo, English

## AI System

The model analyzes crop images and predicts diseases including:

- Tomato Early Blight
- Tomato Late Blight
- Maize Northern Leaf Blight
- Potato and Coffee diseases
- Wheat diseases

Trained on real Ethiopian crop images with 9 disease classes. Accuracy will improve as the field dataset grows.

## Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, FastAPI |
| Database | SQLite (PostgreSQL-ready) |
| Authentication | JWT |
| AI Model | scikit-learn Random Forest + ViT |
| Frontend | Flutter (Android + Web) |
| File handling | Local storage (Cloudinary-ready) |

## Project Structure

```
backend/
  app/
    ai/            AI models, inference, training
    database/      SQLite + SQLAlchemy setup
    models/        User, Prediction, Feedback
    routes/        Auth, predict, users, feedback, language
    schemas/       Pydantic request/response schemas
    utils/         JWT, security, dependencies
    main.py        FastAPI entry point

agrimind_mobile/
  lib/             Flutter app (Android + Web)

screenshots/       UI screenshots
field_data_template.csv   Data collection template
```

## Current Status

**~70% — Working MVP, entering field validation.**

| Component | Progress |
|-----------|----------|
| Backend | 95% |
| Authentication | 95% |
| AI pipeline | 70% |
| Mobile app | 90% |
| Multilingual | 95% |
| Field dataset | 10% |
| Expert validation | 0% |
| Cloud deployment | 0% |

## Roadmap

1. Expand Ethiopian field dataset with agricultural experts
2. Pilot with farmer cooperatives
3. Validate model accuracy against expert diagnoses
4. Deploy to cloud (backend + web)
5. Production hardening

## Contact

**Fethu Mohammed** — Python / FastAPI / React / Flutter Developer
GitHub: [@FETHUMOHAMMED](https://github.com/FETHUMOHAMMED)

# SADA Backend

This backend powers the SADA speech therapy application, with robust endpoints for authentication, exercise tracking, audio uploads, and smart reporting for parents and therapists.

## 🚀 Getting Started

**Install dependencies:**
```bash
pip install -r requirements.txt
```

**Run the FastAPI server:**
```bash
uvicorn app.main:app --reload
```


## 📖 API Documentation
- Access Swagger UI at: http://localhost:8000/docs
- Browse and interact with all API endpoints, including authentication, exercises, progress, and reports.


## 🎤 Audio File Storage
- All uploaded audio files are saved to: `uploads/audio/`
- Access from the frontend via: `/uploads/audio/<filename>` (e.g. `http://localhost:8000/uploads/audio/yourfile.wav`).

## 🖼️ Exercise Images
- Exercise images are uploaded via: `POST /exercises/upload-image`
- Image files are saved to: `uploads/images/`
- Image URLs are served from: `/uploads/images/<filename>`
- `GET /exercises/` now returns `word`, `imageName`, and `imageUrl` for each exercise.


## 🌱 Seeding Exercises
- **Initial Data:**
    - Seed five starter exercises by posting to the development route:
      
      `POST /exercises/seed-exercises` (use Swagger UI or any API client)
    - ⚠️ Remove or secure this route after seeding to avoid accidental data pollution in production.
- Once seeded, visit `GET /exercises/` and you should see the initial exercise data.


## 📊 Progress Reports
- Use `GET /exercises/children/{child_id}/report` to get smart reports for any child:
    - Includes total exercises, total stars, current level, average score, per-category scores, and the last 10 activities.
    - Built for direct use in parent dashboards and visualizations.

---

**Happy Hacking! For questions/contributions, please use Issues or Pull Requests.**

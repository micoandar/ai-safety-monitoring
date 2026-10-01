# AI Workplace Safety Monitoring System

Full-stack web application untuk memonitor kepatuhan penggunaan PPE (Personal Protective Equipment) pada pekerja, menggunakan YOLO11 untuk deteksi objek secara real-time. Mendukung **upload gambar** dan **webcam live detection**.

[![Live Demo](https://img.shields.io/badge/Live%20Demo-ai--safety--monitoring--web.vercel.app-blue?style=flat-square)](https://ai-safety-monitoring-web.vercel.app)
[![API](https://img.shields.io/badge/API-Railway-green?style=flat-square)](https://ai-safety-monitoring-production.up.railway.app/docs)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](#)

---

## Overview

Sistem ini mendeteksi penggunaan helm dan rompi keselamatan pada pekerja menggunakan model YOLO11 yang telah dilatih khusus dengan 5 kelas: `helmet`, `no-helmet`, `vest`, `no-vest`, dan `person`. Hasil deteksi divisualisasikan dengan bounding box dan disimpan ke database untuk monitoring kepatuhan.

**Use case:** Monitoring keselamatan kerja di lokasi konstruksi, pabrik, atau area industri lain yang mewajibkan PPE.

---

## Features

- **Image Detection** - Upload gambar via drag & drop, deteksi PPE dengan bounding box overlay
- **Webcam Live Detection** - Deteksi real-time dari kamera laptop dengan frame throttling (~2.5 FPS)
- **Safety Analysis** - Status kepatuhan otomatis: `Compliant`, `Violation`, atau `Unknown`
- **Dashboard** - Statistik agregat, compliance rate, dan tren 7 hari terakhir
- **Detection History** - Riwayat deteksi dengan pagination, detail, dan hapus
- **REST API** - Endpoint terdokumentasi via Swagger UI

---

## AI Model

Model YOLO11 dengan **5 kelas**:

| Class ID | Name        | Description                     |
| -------- | ----------- | ------------------------------- |
| 0        | `helmet`    | Pekerja memakai helm            |
| 1        | `no-helmet` | Pekerja **tidak** memakai helm  |
| 2        | `no-vest`   | Pekerja **tidak** memakai rompi |
| 3        | `person`    | Pekerja                         |
| 4        | `vest`      | Pekerja memakai rompi           |

**Safety Logic (MVP):**

- Setiap deteksi `no-helmet` atau `no-vest` dianggap pelanggaran
- `compliance_rate = compliant_count / total_person * 100`
- Jika tidak ada `person` terdeteksi -> status `Unknown`

> **Catatan:** Model ini tidak melakukan person-to-PPE association secara individual (setiap PPE tidak diikat ke person tertentu). Compliance dihitung secara agregat. Akan dikembangkan di iterasi berikutnya.

---

## Screenshots

### Dashboard

![Dashboard](screenshots/dashboard.png)

### Detection - Upload Image

![Image Detection](screenshots/detection-image.png)

### Detection - Live Camera

![Webcam Detection](screenshots/detection-webcam.png)

---

## Tech Stack

**Frontend**

- React 19 + Vite
- React Router
- Axios
- Recharts
- Vanilla CSS (design tokens)

**Backend**

- Python 3.11 + FastAPI
- Ultralytics YOLO11
- SQLAlchemy 2.0
- PyMySQL
- Pydantic v2

**Database**

- MySQL (Railway Cloud)

**Deployment**

- Frontend: Vercel
- Backend: Railway (Docker)
- Database: Railway MySQL

---

## System Architecture

+-------------------+
| User Browser |
+---------+---------+
| HTTPS
v
+-------------------------------+
| React Frontend (Vercel) |
| - Dashboard / Detection |
| - Upload + Webcam |
+---------------+---------------+
| REST API (CORS)
v
+-------------------------------+
| FastAPI Backend (Railway) |
| - /api/detection/image |
| - /api/detection/frame |
| - /api/dashboard/stats |
| - Rate limiting + Security |
+---------------+---------------+
| SQLAlchemy
v
+-------------------------------+
| YOLO11 (best.pt) + MySQL |
+-------------------------------+

text

---

## Project Structure

safety-detector/
|
+-- backend/
| +-- ai/best.pt # YOLO11 model
| +-- database/ # SQLAlchemy models
| +-- middleware/ # Rate limit + security headers
| +-- routers/ # API endpoints
| +-- schemas/ # Pydantic schemas
| +-- services/ # YOLO detector + safety analyzer
| +-- config.py
| +-- main.py
| +-- Dockerfile
| +-- requirements.txt
|
+-- frontend/
| +-- src/
| | +-- components/ # Navbar, DetectionBox, dll.
| | +-- pages/ # Dashboard, Detection, History
| | +-- services/api.js
| | +-- App.jsx
| +-- package.json
| +-- vite.config.js
|
+-- screenshots/

text

---

## Installation (Local Development)

### Prerequisites

- Python 3.11+
- Node.js 20+
- MySQL 8+ (atau XAMPP)

### Backend

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
Buat database MySQL:

sql
CREATE DATABASE ppe_safety_monitoring
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
Copy .env.example ke .env, sesuaikan DATABASE_URL.

Letakkan file best.pt di folder backend/ai/.

Jalankan:

bash
uvicorn main:app --reload
Backend: http://localhost:8000
Swagger: http://localhost:8000/docs

Frontend
bash
cd frontend
npm install
cp .env.example .env
npm run dev
Frontend: http://localhost:5173

Environment Variables
Backend (.env)
Variable	Description	Example
DEBUG	Development mode	True / False
DATABASE_URL	MySQL connection string	mysql+pymysql://user:pass@host:3306/db
ALLOWED_ORIGINS	CORS whitelist	http://localhost:5173,https://app.vercel.app
MODEL_PATH	YOLO model path	ai/best.pt
CONFIDENCE_THRESHOLD	YOLO confidence	0.25
MAX_UPLOAD_SIZE_MB	Max upload size	10
RATE_LIMIT_ENABLED	Enable rate limit	True
TRUST_PROXY_HEADERS	Trust X-Forwarded-For	True (production)
Frontend (.env)
Variable	Description
VITE_API_URL	Backend URL (e.g. https://api.example.com)
API Documentation
Interactive docs: https://ai-safety-monitoring-production.up.railway.app/docs

Method	Endpoint	Description
GET	/health	Backend + model status
POST	/api/detection/image	Upload image -> detect -> save to DB
POST	/api/detection/frame	Webcam frame -> detect (no DB save)
GET	/api/detection/history	Paginated detection history
GET	/api/detection/{id}	Detection detail with objects
DELETE	/api/detection/{id}	Delete detection
GET	/api/dashboard/stats	Aggregated statistics + 7-day trend
Database Schema
detections

Column	Type
id	INT PK
detected_at	DATETIME
total_person	INT
compliant_count	INT
violation_count	INT
compliance_rate	FLOAT
overall_status	VARCHAR(20)
detection_objects

Column	Type
id	INT PK
detection_id	INT FK -> detections.id
class_name	VARCHAR(30)
confidence	FLOAT
x1, y1, x2, y2	FLOAT
Deployment
Frontend -> Vercel (auto-deploy from GitHub main)

Backend -> Railway (Docker, auto-deploy from GitHub)

Database -> Railway MySQL (managed)

Environment variables diset di dashboard masing-masing provider.

Future Improvements
□ Person-to-PPE association (deteksi per pekerja, bukan agregat)
□ Model retraining dengan dataset yang lebih besar & beragam
□ Real-time alerting (email/Slack saat violation terdeteksi)
□ Export report ke PDF/CSV
□ Multi-camera support
□ User authentication & role management
□ Video file upload support
□ Model versioning (A/B testing beberapa model)
License
MIT License - bebas digunakan untuk pembelajaran dan referensi.

Author
micoandar - GitHub
```

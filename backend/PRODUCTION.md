# Production Deployment Checklist

## Environment Variables Wajib (Production)

| Variable | Contoh Nilai Production | Catatan |
|---|---|---|
| `DEBUG` | `False` | Aktifkan validasi production |
| `DATABASE_URL` | `mysql+pymysql://user:pass@host:3306/db` | MySQL cloud |
| `ALLOWED_ORIGINS` | `https://your-app.vercel.app` | Tanpa `*` |
| `TRUST_PROXY_HEADERS` | `True` | Render/Railway |
| `MODEL_PATH` | `ai/best.pt` | |
| `RATE_LIMIT_ENABLED` | `True` | |
| `MAX_UPLOAD_SIZE_MB` | `10` | |

## File yang HARUS Ada di Server (bukan via Git)

- `ai/best.pt` — model YOLO11

## Pre-Deploy Checklist

- [ ] `.env` tidak ter-commit
- [ ] `best.pt` tidak ter-commit
- [ ] `DEBUG=False`
- [ ] `ALLOWED_ORIGINS` = domain frontend production
- [ ] `DATABASE_URL` = MySQL cloud
- [ ] `TRUST_PROXY_HEADERS=True`
- [ ] Health check `/health` → `model_loaded: true`
- [ ] CORS preflight `OPTIONS` sukses dari domain frontend
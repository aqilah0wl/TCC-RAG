# 🚀 Panduan Deploy TCC-RAG ke Railway

## Langkah-langkah

---

### 1. Tambahkan file ke repository

Copy file-file berikut ke root folder `TCC-RAG/`:

```
TCC-RAG/
├── railway.json          ← konfigurasi Railway
├── Procfile              ← perintah start server
├── runtime.txt           ← versi Python
├── .env.railway          ← referensi environment variables
└── .github/
    └── workflows/
        └── deploy.yml    ← auto-deploy via GitHub Actions
```

Lalu commit dan push:

```bash
git add .
git commit -m "chore: add Railway deployment config"
git push origin main
```

---

### 2. Buat project di Railway

1. Buka [railway.app](https://railway.app) dan login
2. Klik **New Project → Deploy from GitHub repo**
3. Pilih repository `aqilah0wl/TCC-RAG`
4. Railway akan otomatis detect dan build

---

### 3. Set Environment Variables di Railway

Di Railway Dashboard → pilih project → tab **Variables**, tambahkan:

| Variable | Value |
|---|---|
| `PORT` | `5000` |
| `HOST` | `0.0.0.0` |
| `GEMINI_API_KEY` | *(API key Gemini kamu)* |

---

### 4. Setup Auto-Deploy via GitHub Actions (Opsional)

Untuk deploy otomatis setiap kali push ke `main`:

1. Di Railway Dashboard → **Account Settings → Tokens**
2. Buat token baru, copy nilainya
3. Di GitHub repo → **Settings → Secrets and variables → Actions**
4. Tambahkan secret baru:
   - **Name**: `RAILWAY_TOKEN`
   - **Value**: *(token dari Railway)*

Sekarang setiap `git push` ke `main` akan otomatis trigger deployment! ✅

---

### 5. Dapat URL Publik

Di Railway Dashboard → tab **Settings → Networking**:
- Klik **Generate Domain**
- Kamu akan dapat URL seperti `https://tcc-rag-production.up.railway.app`

---

## ⚠️ Catatan Penting

- **SQLite di Railway**: Data akan **hilang** setiap deploy ulang karena Railway menggunakan ephemeral storage. Untuk production, pertimbangkan migrasi ke PostgreSQL (Railway menyediakan plugin gratis).
- **ONNX model (~80MB)**: Akan didownload otomatis saat pertama kali start. Railway mungkin butuh waktu lebih lama saat cold start pertama.
- **Free tier Railway**: Memberikan $5 credit/bulan, cukup untuk project kecil.

---

## 🔧 Troubleshooting

**Build gagal?**
- Pastikan `backend/requirements.txt` ada dan lengkap
- Cek log build di Railway Dashboard

**App crash saat start?**
- Cek `PORT` sudah di-set ke `5000`
- Pastikan `app.py` menggunakan `os.environ.get('PORT', 5000)`

**AI features tidak jalan?**
- Pastikan `GEMINI_API_KEY` sudah di-set di Railway Variables

# Signate (Anthias) Docker Deployment

Deployment configuration untuk Signate digital signage platform berdasarkan Anthias.

## 🚀 Quick Start

```bash
# Jalankan deployment script
cd /mnt/g/khoirul/signate2
./docker/deploy.sh
```

## 📋 Manual Deployment

```bash
# 1. Pindah ke root directory
cd /mnt/g/khoirul/signate2

# 2. Start semua services
docker-compose -f docker/docker-compose.yml up -d

# 3. Install Bootstrap dependency
docker-compose -f docker/docker-compose.yml exec anthias-server npm install bootstrap@5.3.3

# 4. Restart server untuk rebuild
docker-compose -f docker/docker-compose.yml restart anthias-server

# 5. Tunggu webpack build selesai (1-2 menit)
```

## 🌐 Access

- **Dashboard:** http://localhost:8000/
- **Direct Server:** http://localhost:9000/ (development)

## 🔧 Management Commands

```bash
# Lihat status services
docker-compose -f docker/docker-compose.yml ps

# Lihat logs
docker-compose -f docker/docker-compose.yml logs -f

# Stop services
docker-compose -f docker/docker-compose.yml down

# Restart specific service
docker-compose -f docker/docker-compose.yml restart anthias-server
```

## 🏗️ Services

- **anthias-server**: Django backend (port 9000)
- **anthias-websocket**: Real-time communication
- **anthias-celery**: Background task processing
- **anthias-nginx**: Web gateway (port 8000)
- **redis**: Cache dan message broker

## 📁 Structure

```
signate2/
├── docker/
│   ├── docker-compose.yml    # Main deployment config
│   ├── deploy.sh            # Automated deployment script
│   └── README.md           # This file
├── project/
│   ├── backend/            # Anthias backend source
│   └── frontend/           # Future frontend development
└── deployment/             # Alternative deployment configs
```

## ⚠️ Important Notes

1. **Bootstrap Dependency**: Default Anthias membutuhkan Bootstrap npm package
2. **Webpack Build**: Tunggu webpack selesai compile sebelum akses dashboard
3. **Port 8000**: Pastikan port tidak digunakan aplikasi lain
4. **Redis**: Menggunakan Redis Alpine tanpa password untuk development

## 🐛 Troubleshooting

**502 Bad Gateway:**
- Tunggu webpack build selesai
- Restart anthias-server service

**Bootstrap SCSS errors:**
- Install Bootstrap: `npm install bootstrap@5.3.3`
- Restart server untuk rebuild

**Port already in use:**
- Stop layanan lain di port 8000
- Atau ubah port di docker-compose.yml
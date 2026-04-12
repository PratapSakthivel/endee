# ErrorLens Deployment Guide

## 🚀 Production Deployment Guide

This guide provides step-by-step instructions for deploying ErrorLens to production environments.

---

## 📋 Pre-Deployment Checklist

- [ ] All 9 development phases completed
- [ ] Manual testing checklist completed
- [ ] Performance benchmarks met
- [ ] Documentation reviewed and accurate
- [ ] Environment variables configured
- [ ] Groq API key obtained
- [ ] Docker and Docker Compose installed
- [ ] Domain name configured (if applicable)

---

## 🏗️ Deployment Options

### Option 1: Docker Compose (Recommended)

**Best for**: Full-stack deployment with all services containerized

**Requirements**:
- Docker 20.10+
- Docker Compose 2.0+
- 8GB+ RAM
- 10GB+ disk space

**Steps**:

1. **Clone Repository**
```bash
git clone https://github.com/PratapSakthivel/endee.git
cd endee
```

2. **Configure Environment**
```bash
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
nano .env
```

3. **Build and Start Services**
```bash
docker compose up --build -d
```

4. **Verify Deployment**
```bash
python scripts/verify_deployment.py
```

5. **Access Services**
- Frontend: http://localhost:8501
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Endee: http://localhost:8080

**Monitoring**:
```bash
# View logs
docker compose logs -f

# Check service status
docker compose ps

# Restart services
docker compose restart

# Stop services
docker compose down
```

---

### Option 2: Render.com (Free Tier)

**Best for**: Quick deployment without infrastructure management

**Steps**:

1. **Push to GitHub**
```bash
git push origin main
```

2. **Create Render Account**
- Go to https://render.com
- Sign up with GitHub

3. **Deploy Backend**
- New → Web Service
- Connect your repository
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
- **Environment Variables**:
  - `GROQ_API_KEY`: your_groq_api_key
  - `ENDEE_URL`: your_endee_instance_url
  - `EMBEDDING_MODEL`: all-MiniLM-L6-v2

4. **Deploy Frontend**
- New → Web Service
- Connect your repository
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `streamlit run frontend/streamlit_app.py --server.port $PORT --server.address 0.0.0.0`
- **Environment Variables**:
  - `API_URL`: your_backend_url

5. **Deploy Endee**
- Use Render's Docker deployment or external Endee instance
- Update `ENDEE_URL` in backend environment

---

### Option 3: Railway.app

**Best for**: Automatic deployment with GitHub integration

**Steps**:

1. **Create Railway Account**
- Go to https://railway.app
- Sign up with GitHub

2. **New Project**
- New Project → Deploy from GitHub
- Select your repository

3. **Configure Services**
- Railway auto-detects Python
- Add environment variables:
  - `GROQ_API_KEY`
  - `ENDEE_URL`
  - `EMBEDDING_MODEL`

4. **Deploy**
- Railway automatically builds and deploys
- Get public URL from dashboard

---

### Option 4: AWS/GCP/Azure

**Best for**: Enterprise deployment with full control

**Architecture**:
- **Compute**: EC2/Compute Engine/VM
- **Container**: ECS/GKE/AKS
- **Database**: Endee on dedicated instance
- **Load Balancer**: ALB/Cloud Load Balancing
- **Storage**: S3/Cloud Storage for logs

**Steps**:

1. **Provision Infrastructure**
```bash
# Example for AWS EC2
aws ec2 run-instances \
  --image-id ami-xxxxx \
  --instance-type t3.large \
  --key-name your-key \
  --security-groups errorlens-sg
```

2. **Install Dependencies**
```bash
ssh -i your-key.pem ubuntu@your-instance
sudo apt update
sudo apt install docker.io docker-compose python3-pip
```

3. **Deploy Application**
```bash
git clone https://github.com/PratapSakthivel/endee.git
cd endee
cp .env.example .env
# Configure .env
docker compose up -d
```

4. **Configure Load Balancer**
- Point to backend:8000 and frontend:8501
- Configure SSL/TLS certificates
- Set up health checks

---

## 🔒 Security Considerations

### Environment Variables
- **Never commit** `.env` file to git
- Use secrets management (AWS Secrets Manager, HashiCorp Vault)
- Rotate API keys regularly

### Network Security
- Use HTTPS/TLS for all connections
- Configure firewall rules (allow only necessary ports)
- Use VPC/private networks for internal communication

### Authentication
- Add authentication layer for production
- Implement rate limiting
- Use API keys for backend access

### Docker Security
- Run containers as non-root user (already configured)
- Keep base images updated
- Scan images for vulnerabilities

---

## 📊 Monitoring & Logging

### Health Checks
```bash
# Backend health
curl http://localhost:8000/health

# Endee health
curl http://localhost:8080/health

# Frontend health
curl http://localhost:8501/_stcore/health
```

### Logging
```bash
# Docker Compose logs
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f endee

# Application logs
tail -f /app/logs/errorlens.log
```

### Metrics
- Monitor CPU/Memory usage
- Track API response times
- Monitor Endee vector count
- Track search latency

---

## 🔄 Backup & Recovery

### Backup Endee Data
```bash
# Export vectors
curl -X GET http://localhost:8080/collections/error_logs/export > backup.json

# Backup with Docker
docker exec endee-server tar czf /backup/endee-data.tar.gz /data
docker cp endee-server:/backup/endee-data.tar.gz ./backups/
```

### Restore Data
```bash
# Import vectors
curl -X POST http://localhost:8080/collections/error_logs/import \
  -H "Content-Type: application/json" \
  -d @backup.json
```

---

## 🚨 Troubleshooting

### Backend Won't Start
```bash
# Check logs
docker compose logs backend

# Common issues:
# - Missing GROQ_API_KEY
# - Endee not accessible
# - Port 8000 already in use

# Solutions:
# - Verify .env file
# - Check Endee health
# - Change port in docker-compose.yml
```

### Frontend Won't Load
```bash
# Check logs
docker compose logs frontend

# Common issues:
# - Backend not accessible
# - Port 8501 already in use

# Solutions:
# - Verify API_URL in .env
# - Check backend health
# - Change port in docker-compose.yml
```

### Endee Connection Issues
```bash
# Check Endee status
docker ps | grep endee

# Restart Endee
docker restart endee-server

# Check Endee logs
docker logs endee-server
```

### Performance Issues
```bash
# Check resource usage
docker stats

# Increase memory limits in docker-compose.yml
# Scale services
docker compose up --scale backend=2
```

---

## 📈 Scaling

### Horizontal Scaling
```yaml
# docker-compose.yml
services:
  backend:
    deploy:
      replicas: 3
    
  frontend:
    deploy:
      replicas: 2
```

### Load Balancing
```bash
# Use nginx as reverse proxy
upstream backend {
    server backend1:8000;
    server backend2:8000;
    server backend3:8000;
}
```

### Database Scaling
- Use Endee clustering for high availability
- Implement read replicas
- Use caching layer (Redis)

---

## 🎯 Production Checklist

### Pre-Launch
- [ ] All tests passing
- [ ] Performance benchmarks met
- [ ] Security audit completed
- [ ] SSL/TLS certificates configured
- [ ] Monitoring set up
- [ ] Backup strategy implemented
- [ ] Documentation reviewed

### Launch
- [ ] Deploy to production
- [ ] Verify all services running
- [ ] Test critical workflows
- [ ] Monitor for errors
- [ ] Announce to users

### Post-Launch
- [ ] Monitor performance
- [ ] Collect user feedback
- [ ] Address issues promptly
- [ ] Plan improvements
- [ ] Regular backups

---

## 📞 Support

### Getting Help
- **Documentation**: README.md, API docs at /docs
- **Issues**: GitHub Issues
- **Community**: Endee Discord/Slack

### Reporting Issues
1. Check existing issues
2. Provide detailed description
3. Include logs and error messages
4. Specify environment details

---

## 🎉 Deployment Complete!

Once deployed, ErrorLens provides:
- ✅ Intelligent semantic log analysis
- ✅ AI-powered root cause suggestions
- ✅ Real-time error monitoring
- ✅ Scalable vector search with Endee
- ✅ Production-ready architecture

**Next Steps**:
1. Upload your first log files
2. Explore semantic search
3. Try RAG analysis
4. Monitor your error patterns

---

**ErrorLens Deployment Guide v1.0**
*Production-ready deployment for intelligent log analysis*
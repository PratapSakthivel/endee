# 🚀 ErrorLens - Render.com Deployment Guide

## Quick Deployment to Render.com (Free Tier)

This guide will help you deploy ErrorLens to Render.com in under 10 minutes!

---

## 📋 Prerequisites

1. **GitHub Account** - Your code is already pushed to GitHub ✅
2. **Render.com Account** - Free (we'll create this)
3. **Groq API Key** - For AI-powered analysis (you already have this)

---

## 🎯 Step-by-Step Deployment

### Step 1: Create Render Account (2 minutes)

1. Go to **https://render.com**
2. Click **"Get Started for Free"**
3. Sign up with your **GitHub account** (PratapSakthivel)
4. Authorize Render to access your GitHub repositories

### Step 2: Deploy Backend API (3 minutes)

1. **From Render Dashboard**, click **"New +"** → **"Web Service"**

2. **Connect Repository**:
   - Select **"endee"** repository
   - Click **"Connect"**

3. **Configure Backend Service**:
   ```
   Name: errorlens-backend
   Region: Oregon (US West)
   Branch: master
   Root Directory: (leave blank)
   Runtime: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: uvicorn backend.main:app --host 0.0.0.0 --port $PORT
   Plan: Free
   ```

4. **Add Environment Variables** (Click "Advanced" → "Add Environment Variable"):
   ```
   GROQ_API_KEY = your_groq_api_key_here
   EMBEDDING_MODEL = all-MiniLM-L6-v2
   PYTHON_VERSION = 3.10.0
   ```
   
   **Important**: Replace `your_groq_api_key_here` with your actual Groq API key from https://console.groq.com
   
   **Note**: We'll add ENDEE_URL after deploying Endee

5. Click **"Create Web Service"**

6. **Wait for deployment** (3-5 minutes)
   - Render will build and deploy your backend
   - You'll see build logs in real-time
   - Once complete, you'll get a URL like: `https://errorlens-backend.onrender.com`

7. **Test Backend**:
   - Open: `https://errorlens-backend.onrender.com/health`
   - Should show: `{"status":"healthy",...}`
   - Open: `https://errorlens-backend.onrender.com/docs`
   - Should show interactive API documentation

### Step 3: Deploy Endee Vector Database (3 minutes)

1. **From Render Dashboard**, click **"New +"** → **"Web Service"**

2. **Configure Endee Service**:
   ```
   Name: errorlens-endee
   Region: Oregon (US West)
   Runtime: Docker
   Image URL: endeeio/endee-server:latest
   Plan: Free
   ```

3. **Add Environment Variables**:
   ```
   NDD_DATA_PATH = /data
   NDD_RAM_LIMIT = 512MB
   PORT = 8080
   ```

4. **Add Persistent Disk** (Important!):
   - Click "Add Disk"
   - Name: `endee-data`
   - Mount Path: `/data`
   - Size: 1 GB

5. Click **"Create Web Service"**

6. **Wait for deployment** (2-3 minutes)
   - Once complete, you'll get a URL like: `https://errorlens-endee.onrender.com`

7. **Test Endee**:
   - Open: `https://errorlens-endee.onrender.com/health`
   - Should show: `{"status":"ok",...}`

8. **Update Backend Environment**:
   - Go back to **errorlens-backend** service
   - Click **"Environment"** tab
   - Add new variable:
     ```
     ENDEE_URL = https://errorlens-endee.onrender.com/api/v1
     ```
   - Click **"Save Changes"**
   - Backend will automatically redeploy

### Step 4: Deploy Frontend (2 minutes)

1. **From Render Dashboard**, click **"New +"** → **"Web Service"**

2. **Connect Repository**:
   - Select **"endee"** repository again
   - Click **"Connect"**

3. **Configure Frontend Service**:
   ```
   Name: errorlens-frontend
   Region: Oregon (US West)
   Branch: master
   Root Directory: (leave blank)
   Runtime: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: streamlit run frontend/streamlit_app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true
   Plan: Free
   ```

4. **Add Environment Variables**:
   ```
   API_URL = https://errorlens-backend.onrender.com
   PYTHON_VERSION = 3.10.0
   ```

5. Click **"Create Web Service"**

6. **Wait for deployment** (3-5 minutes)
   - Once complete, you'll get a URL like: `https://errorlens-frontend.onrender.com`

### Step 5: Verify Deployment (1 minute)

1. **Open Frontend URL**: `https://errorlens-frontend.onrender.com`

2. **Check System Status**:
   - All components should show green ✅
   - Backend API: Online
   - Vector DB: Connected
   - AI Model: Loaded

3. **Test Functionality**:
   - Go to **"Ingest"** page
   - Upload a sample log file
   - Go to **"Search"** page
   - Try a search query
   - Go to **"Root Cause"** page
   - Test AI analysis

---

## 🎉 Deployment Complete!

Your ErrorLens application is now live on Render.com!

### 📍 Your Live URLs:

- **Frontend (Main App)**: `https://errorlens-frontend.onrender.com`
- **Backend API**: `https://errorlens-backend.onrender.com`
- **API Documentation**: `https://errorlens-backend.onrender.com/docs`
- **Endee Database**: `https://errorlens-endee.onrender.com`

---

## ⚠️ Important Notes for Free Tier

### Free Tier Limitations:
- **Services spin down after 15 minutes of inactivity**
- **First request after spin-down takes 30-60 seconds** (cold start)
- **750 hours/month free** (enough for continuous operation)
- **Limited RAM**: 512MB per service

### Keeping Services Active:
You can use a service like **UptimeRobot** or **Cron-job.org** to ping your services every 10 minutes:
```
Ping URL: https://errorlens-backend.onrender.com/health
Interval: Every 10 minutes
```

### Upgrading to Paid Plan:
If you need:
- No cold starts
- More RAM (up to 16GB)
- Custom domains
- Better performance

Upgrade to **Starter Plan** ($7/month per service)

---

## 🔧 Managing Your Deployment

### View Logs:
1. Go to Render Dashboard
2. Click on service name
3. Click **"Logs"** tab
4. View real-time logs

### Update Deployment:
1. Push changes to GitHub master branch
2. Render automatically detects and redeploys
3. Or manually trigger: Click **"Manual Deploy"** → **"Deploy latest commit"**

### Environment Variables:
1. Click service name
2. Click **"Environment"** tab
3. Add/Edit/Delete variables
4. Click **"Save Changes"**

### Restart Service:
1. Click service name
2. Click **"Manual Deploy"** → **"Clear build cache & deploy"**

---

## 🐛 Troubleshooting

### Backend Shows "Unhealthy":
- Check if ENDEE_URL is correct
- Verify GROQ_API_KEY is set
- Check logs for errors

### Frontend Can't Connect to Backend:
- Verify API_URL environment variable
- Check if backend is running
- Test backend health endpoint

### Endee Connection Failed:
- Check if Endee service is running
- Verify disk is mounted at `/data`
- Check Endee logs

### Cold Start Issues:
- First request after inactivity takes 30-60 seconds
- This is normal for free tier
- Consider using UptimeRobot to keep services warm

---

## 📊 Monitoring Your Deployment

### Render Dashboard:
- **Metrics**: CPU, Memory, Request count
- **Logs**: Real-time application logs
- **Events**: Deployment history

### Application Health:
- Backend: `https://errorlens-backend.onrender.com/health`
- Endee: `https://errorlens-endee.onrender.com/health`

---

## 🎯 Next Steps

1. **Share Your App**: Send the frontend URL to users
2. **Upload Logs**: Start ingesting your application logs
3. **Test Features**: Try semantic search and AI analysis
4. **Monitor Usage**: Check Render dashboard for metrics
5. **Collect Feedback**: Gather user feedback for improvements

---

## 📞 Support

### Render Support:
- **Documentation**: https://render.com/docs
- **Community**: https://community.render.com
- **Status**: https://status.render.com

### ErrorLens Support:
- **GitHub Issues**: https://github.com/PratapSakthivel/endee/issues
- **Email**: pratapssakthivel@gmail.com

---

## 🎉 Congratulations!

You've successfully deployed ErrorLens to production! 🚀

Your intelligent log analysis system is now accessible worldwide and ready to help analyze errors with AI-powered insights.

**Built with ❤️ by Pratap Sakthivel | VSB Engineering College | 2026**

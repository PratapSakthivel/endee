# ErrorLens Setup Instructions

## ⚠️ IMPORTANT: Python Version Requirement

**ErrorLens requires 64-bit Python 3.10 or higher.**

Your current Python is **32-bit** which is not compatible with PyTorch (required for sentence-transformers).

### Check Your Python Version

```bash
python -c "import sys; print(f'Python {sys.version}'); print(f'Architecture: {sys.maxsize > 2**32 and \"64-bit\" or \"32-bit\"}')"
```

## Solution Options

### Option 1: Install 64-bit Python (Recommended)

1. Download Python 3.11 (64-bit) from: https://www.python.org/downloads/
   - **Important**: Select "Windows installer (64-bit)"
   - During installation, check "Add Python to PATH"

2. After installation, verify:
   ```bash
   python --version
   python -c "import sys; print(sys.maxsize > 2**32)"  # Should print: True
   ```

3. Then run the setup:
   ```bash
   # Create virtual environment with 64-bit Python
   python -m venv venv
   
   # Activate
   venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

### Option 2: Use Conda (Alternative)

Conda handles 64-bit Python and PyTorch automatically:

```bash
# Install Miniconda: https://docs.conda.io/en/latest/miniconda.html

# Create environment
conda create -n errorlens python=3.11
conda activate errorlens

# Install PyTorch
conda install pytorch torchvision torchaudio cpuonly -c pytorch

# Install other dependencies
pip install -r requirements.txt
```

### Option 3: Cloud Development (No Local Install)

Use GitHub Codespaces or Google Colab for development:
- GitHub Codespaces: https://github.com/codespaces
- Google Colab: https://colab.research.google.com/

## After Installing 64-bit Python

1. **Create .env file:**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your Groq API key:
   ```
   GROQ_API_KEY=your_actual_groq_api_key_here
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   
   This will take 3-5 minutes to download all packages.

3. **Verify Endee is running:**
   ```bash
   curl http://localhost:8080/health
   ```
   
   Should return: `{"status": "ok"}`

4. **Ready for Phase 1!**

## Current Status

- ✅ Phase 0: Project structure created
- ✅ Configuration files ready
- ✅ Dependencies specified
- ⏳ Waiting for 64-bit Python installation

## Need Help?

If you encounter issues:
1. Verify you have 64-bit Python installed
2. Check that Endee is running on port 8080
3. Ensure your Groq API key is valid

## Next Steps

Once 64-bit Python is installed and dependencies are working:
1. Test the setup
2. Commit Phase 0 to git
3. Move to Phase 1: Log Parser Implementation

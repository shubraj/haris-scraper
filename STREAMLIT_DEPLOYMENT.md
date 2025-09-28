# Streamlit Cloud Deployment Guide

## 🚀 Deployment Steps

### 1. Environment Variables
Set these in your Streamlit Cloud app settings:

```
OPENAI_API_KEY=your_openai_api_key_here
HCTX_USERNAME=your_harris_county_username
HCTX_PASSWORD=your_harris_county_password
```

### 2. Required Files
Ensure these files are in your repository root:
- `app.py` - Main Streamlit application
- `requirements.txt` - Python dependencies
- `packages.txt` - System packages
- `postBuild` - Build script
- `postInstall` - Installation script
- `.streamlit/config.toml` - Streamlit configuration

### 3. System Dependencies
The `packages.txt` includes:
- Playwright browser dependencies
- Tesseract OCR engine
- Additional system libraries

### 4. Build Process
1. **postBuild** runs after pip install:
   - Installs Playwright browsers
   - Installs system dependencies
   - Creates necessary directories
   - Verifies package installations

2. **postInstall** runs after postBuild:
   - Fallback Playwright installation
   - System dependency installation
   - Package verification

### 5. Application Features
- ✅ Harris County property records scraping
- ✅ HCAD property search
- ✅ PDF download functionality
- ✅ Address extraction with OpenAI
- ✅ PDF OCR processing
- ✅ Comprehensive logging

### 6. Troubleshooting

#### Common Issues:
1. **Playwright browser not found**
   - Check `packages.txt` includes all browser dependencies
   - Verify `postBuild` runs `playwright install chromium`

2. **Tesseract OCR not working**
   - Ensure `tesseract-ocr` and `tesseract-ocr-eng` in `packages.txt`
   - Check system PATH includes tesseract

3. **Authentication errors**
   - Verify environment variables are set correctly
   - Check credentials in Streamlit Cloud app settings

4. **Memory issues**
   - Large PDF processing may require more memory
   - Consider reducing batch sizes for bulk operations

#### Logs Location:
- Application logs: `logs/` directory
- Streamlit logs: Available in Streamlit Cloud dashboard

### 7. Performance Optimization
- Uses session-based HTTP requests for efficiency
- Implements singleton pattern for scraper instances
- Rotating log files to prevent disk space issues
- Chunked PDF downloads for large files

### 8. Security Notes
- Environment variables are encrypted in Streamlit Cloud
- No sensitive data stored in repository
- Session-based authentication for Harris County website
- Secure file handling for downloads

## 📋 Pre-deployment Checklist

- [ ] Environment variables configured
- [ ] All required files present
- [ ] `packages.txt` includes all dependencies
- [ ] `postBuild` and `postInstall` scripts executable
- [ ] `.streamlit/config.toml` configured
- [ ] Repository pushed to GitHub
- [ ] Streamlit Cloud app created and linked

## 🔧 Maintenance

### Regular Tasks:
1. Monitor log files for errors
2. Check environment variable validity
3. Update dependencies as needed
4. Monitor memory usage for large operations

### Updates:
1. Test changes locally first
2. Update version numbers in requirements.txt
3. Test deployment in Streamlit Cloud
4. Monitor for any new dependency issues

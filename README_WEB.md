# Battlecard Generator - Web Applications

This repository contains three different web application implementations of the Battlecard Generator:

1. **Streamlit** - Easiest to deploy and use
2. **Flask** - Professional web application with custom UI
3. **FastAPI** - Modern async API with automatic documentation

## 🚀 Quick Start

### Prerequisites

1. **API Keys Setup**: Make sure you have the following environment variables set:
   ```bash
   export GOOGLE_API_KEY="your_google_api_key"
   export GOOGLE_API_KEY_2="your_second_google_api_key"
   export GOOGLE_CSE_ID="your_cse_id"
   export GOOGLE_CSE_ID_2="your_second_cse_id"
   export LLM_API_KEY="your_groq_api_key"
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## 📊 Option 1: Streamlit (Recommended for Beginners)

### Run Locally
```bash
streamlit run streamlit_app.py
```

### Deploy to Streamlit Cloud
1. Push your code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repository
4. Deploy!

**Pros**: 
- Easiest to deploy
- Built-in UI components
- Free hosting on Streamlit Cloud
- No frontend/backend complexity

**Cons**: 
- Limited customization
- May have usage limits

## 🌐 Option 2: Flask (Professional Web App)

### Run Locally
```bash
python flask_app.py
```
Then visit `http://localhost:5000`

### Deploy to Render (Free)
1. Create a `render.yaml` file:
```yaml
services:
  - type: web
    name: battlecard-generator
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python flask_app.py
    envVars:
      - key: GOOGLE_API_KEY
        value: your_google_api_key
      - key: GOOGLE_API_KEY_2
        value: your_second_google_api_key
      - key: GOOGLE_CSE_ID
        value: your_cse_id
      - key: GOOGLE_CSE_ID_2
        value: your_second_cse_id
      - key: LLM_API_KEY
        value: your_groq_api_key
```

2. Push to GitHub and connect to Render

### Deploy to Heroku
1. Create a `Procfile`:
```
web: python flask_app.py
```

2. Deploy using Heroku CLI or GitHub integration

**Pros**: 
- Full control over UI/UX
- Professional appearance
- Scalable
- Custom styling

**Cons**: 
- More complex setup
- Requires web framework knowledge

## ⚡ Option 3: FastAPI (Modern API)

### Run Locally
```bash
python fastapi_app.py
```
Then visit `http://localhost:8000`

### API Documentation
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Deploy to Railway (Free)
1. Push to GitHub
2. Connect to Railway
3. Set environment variables
4. Deploy!

### Deploy to Render
Similar to Flask deployment, but use:
```bash
uvicorn fastapi_app:app --host 0.0.0.0 --port $PORT
```

**Pros**: 
- Modern async support
- Automatic API documentation
- Type safety with Pydantic
- High performance

**Cons**: 
- More complex than Streamlit
- Requires API knowledge

## 📁 File Structure

```
battlecards/
├── battlecard_main.py          # Core battlecard logic
├── streamlit_app.py            # Streamlit web app
├── flask_app.py               # Flask web app
├── fastapi_app.py             # FastAPI web app
├── templates/
│   └── index.html             # HTML template for Flask/FastAPI
├── requirements.txt           # Core dependencies
├── requirements_web.txt       # Web app dependencies
├── README.md                  # Main README
└── README_WEB.md             # This file
```

## 🔧 Configuration

### Environment Variables
All applications use the same environment variables:

- `GOOGLE_API_KEY`: Primary Google Custom Search API key
- `GOOGLE_API_KEY_2`: Secondary Google API key (fallback)
- `GOOGLE_CSE_ID`: Primary Google Custom Search Engine ID
- `GOOGLE_CSE_ID_2`: Secondary CSE ID (fallback)
- `LLM_API_KEY`: Groq API key for LLM calls

### Customization

#### Streamlit
- Modify `streamlit_app.py` for UI changes
- Add new sections in the tabs
- Customize styling with `st.markdown()` and CSS

#### Flask
- Modify `templates/index.html` for UI changes
- Add new routes in `flask_app.py`
- Customize styling in the HTML template

#### FastAPI
- Modify `fastapi_app.py` for API changes
- Add new endpoints
- Update Pydantic models for request/response

## 🚀 Deployment Recommendations

### For Beginners
**Use Streamlit** - Easiest deployment and maintenance

### For Production
**Use Flask or FastAPI** - More control and scalability

### For API-First Approach
**Use FastAPI** - Best for building APIs and integrations

## 🔍 Usage

1. **Enter Company Information**:
   - Company Name (e.g., "Apple Inc.")
   - Company Website (e.g., "apple.com")

2. **Generate Battlecard**:
   - Click "Generate Battlecard"
   - Wait for processing (2-5 minutes)
   - View results in organized tabs

3. **Download Results**:
   - Download as Markdown file
   - Use in your business intelligence tools

## 🛠️ Troubleshooting

### Common Issues

1. **API Rate Limits**:
   - The apps include retry logic for rate limits
   - Consider upgrading API plans for higher limits

2. **No Results Found**:
   - Check company name spelling
   - Verify website domain
   - Try different company variations

3. **Deployment Issues**:
   - Ensure all environment variables are set
   - Check port configurations
   - Verify dependency installations

### Support
- Check the main `README.md` for core functionality
- Review API documentation for your chosen platform
- Test locally before deploying

## 📈 Performance Tips

1. **Reduce API Calls**:
   - The apps already optimize for minimal API usage
   - Consider caching results for repeated queries

2. **Improve Response Times**:
   - Use secondary API keys for fallback
   - Consider async processing for multiple requests

3. **Scale for Production**:
   - Add database for result caching
   - Implement user authentication
   - Add rate limiting for public access

## 🎯 Next Steps

1. **Choose your preferred platform**
2. **Set up API keys**
3. **Deploy to your chosen hosting service**
4. **Customize the UI/UX as needed**
5. **Monitor usage and optimize performance**

Happy battlecard generating! 🚀 
# Battlecard Generator

This tool generates a battlecard for a given company using Google Custom Search API and an LLM (e.g., Llama 70B). It outputs a markdown file with four sections: Company Overview, Recent News, Leadership Changes, and Mergers & Acquisitions.

## 🔐 Security First!

**IMPORTANT**: This tool requires API keys that should never be committed to version control. The project includes a `.gitignore` file to protect your secrets.

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure API keys:**
   Edit the `.env` file with your API keys:
   ```bash
   GOOGLE_API_KEY=your_google_api_key_here
   GOOGLE_API_KEY_2=your_second_google_api_key_here  # optional
   GOOGLE_CSE_ID=your_cse_id_here
   GOOGLE_CSE_ID_2=your_second_cse_id_here  # optional
   LLM_API_KEY=your_groq_api_key_here
   ```

   **Required API Keys:**
   - `GOOGLE_API_KEY`: Your Google Custom Search API key
   - `GOOGLE_CSE_ID`: Your Google Custom Search Engine ID  
   - `LLM_API_KEY`: Your Groq API key

   **Optional (for fallback):**
   - `GOOGLE_API_KEY_2`: Secondary Google API key
   - `GOOGLE_CSE_ID_2`: Secondary CSE ID

## Usage

### Command Line Interface
```bash
python battlecard_main.py
```

### Web Applications
- **Streamlit**: `streamlit run streamlit_app.py`
- **Flask**: `python flask_app.py`
- **FastAPI**: `uvicorn fastapi_app:app --reload`

See `README_WEB.md` for detailed web deployment instructions.

## Output

- `battlecard_{company_name}.md`: The generated battlecard in markdown format

## Security Features

- ✅ `.gitignore` excludes `.env` files and sensitive data
- ✅ Environment variable validation on startup
- ✅ No hardcoded API keys in source code
- ✅ Secure environment variable handling

## Getting API Keys

1. **Google Custom Search API**: https://console.cloud.google.com/apis/credentials
2. **Google Custom Search Engine**: https://cse.google.com/cse/
3. **Groq API**: https://console.groq.com/

## Notes

- The script uses only the snippets from Google search results for summarization
- If information is missing, the script will indicate so in the output
- You can customize the LLM prompts or search queries in `battlecard_main.py` as needed
- The tool includes retry logic for API rate limits and fallback API keys

## Features

- Uses Google Custom Search API with the 'daterestrict' parameter for recency filtering
- Automatic fallback to unrestricted search if site-restricted results are insufficient
- Deduplication of overlapping content between sections
- Rate limit handling with automatic retries
- Multiple web interface options (Streamlit, Flask, FastAPI) 
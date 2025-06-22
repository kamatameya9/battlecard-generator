from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Dict, Any, Optional
import os
import sys
from datetime import datetime
import io
import asyncio
from contextlib import asynccontextmanager

# Add the current directory to Python path to import battlecard_main functions
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import functions from battlecard_main
from battlecard_main import (
    get_queries, get_prompts, google_search, 
    call_llm_with_retry, deduplicate_sections, mask_sensitive_info
)

# Pydantic models for request/response
class BattlecardRequest(BaseModel):
    company_name: str
    company_website: Optional[str] = None

class BattlecardResponse(BaseModel):
    success: bool
    company_name: str
    battlecard: str
    sections: Dict[str, str]
    generated_at: str

class ErrorResponse(BaseModel):
    error: str

def secure_error_detail(error):
    """Return a sanitized error detail that doesn't expose sensitive information"""
    error_msg = str(error)
    masked_msg = mask_sensitive_info(error_msg)
    
    # Provide user-friendly error messages
    if "Google Custom Search API" in masked_msg:
        return "Google search service temporarily unavailable. Please try again later."
    elif "Groq LLM API" in masked_msg:
        return "AI processing service temporarily unavailable. Please try again later."
    elif "Missing required environment variables" in masked_msg:
        return "Server configuration error. Please contact administrator."
    else:
        return "An unexpected error occurred. Please try again later."

# FastAPI app with lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Battlecard Generator API starting up...")
    yield
    # Shutdown
    print("🛑 Battlecard Generator API shutting down...")

app = FastAPI(
    title="Battlecard Generator API",
    description="Generate comprehensive battlecards for any company using AI-powered web search and analysis",
    version="1.0.0",
    lifespan=lifespan
)

# Templates
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    try:
        return templates.TemplateResponse("index.html", {"request": request})
    except Exception:
        # Fallback if template doesn't exist or there's an error
        return HTMLResponse("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Battlecard Generator API</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .container { max-width: 800px; margin: 0 auto; }
                .endpoint { background: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px; }
                code { background: #e0e0e0; padding: 2px 5px; border-radius: 3px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📊 Battlecard Generator API</h1>
                <p>Welcome to the Battlecard Generator API. Use the following endpoints:</p>
                
                <div class="endpoint">
                    <h3>Generate Battlecard</h3>
                    <p><code>POST /generate</code></p>
                    <p>Generate a battlecard for a company.</p>
                    <p><strong>Body:</strong> {"company_name": "Company Name", "company_website": "company.com" (optional)}</p>
                </div>
                
                <div class="endpoint">
                    <h3>Download Battlecard</h3>
                    <p><code>POST /download</code></p>
                    <p>Download a battlecard as a markdown file.</p>
                </div>
                
                <div class="endpoint">
                    <h3>Health Check</h3>
                    <p><code>GET /health</code></p>
                    <p>Check if the API is running.</p>
                </div>
                
                <div class="endpoint">
                    <h3>API Documentation</h3>
                    <p><code>GET /docs</code></p>
                    <p>Interactive API documentation.</p>
                </div>
                
                <p><a href="/docs">View Interactive API Documentation</a></p>
            </div>
        </body>
        </html>
        """)

@app.post("/generate", response_model=BattlecardResponse)
async def generate_battlecard(request: BattlecardRequest, background_tasks: BackgroundTasks):
    """
    Generate a battlecard for the specified company.
    
    - **company_name**: The name of the company
    - **company_website**: The company's website domain (optional)
    """
    try:
        company_name = request.company_name.strip()
        company_website = request.company_website.strip() if request.company_website else None
        
        if not company_name:
            raise HTTPException(status_code=400, detail="Please provide a company name")
        
        # Run the battlecard generation in a thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, generate_battlecard_sync, company_name, company_website)
        
        return BattlecardResponse(
            success=True,
            company_name=company_name,
            battlecard=result['battlecard'],
            sections=result['sections'],
            generated_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=secure_error_detail(e))

def generate_battlecard_sync(company_name: str, company_website: Optional[str] = None) -> Dict[str, Any]:
    """Synchronous function to generate battlecard (runs in thread pool)"""
    # Get queries and prompts
    queries = get_queries(company_name, company_website)
    prompts = get_prompts(company_name, company_website)
    sections = {}
    
    # Process each section
    for section, qinfo in queries.items():
        search_type = "site-restricted" if company_website else "unrestricted"
        print(f"Processing {section} ({search_type})...")
        
        # If we have a website, try restricted search first, then fallback to unrestricted
        if company_website:
            restricted_snippets = google_search(qinfo['query'], qinfo['daterestrict'])
            
            # Only do unrestricted search if we have some restricted results but need more
            if len(restricted_snippets) > 0 and len(restricted_snippets) < 10:
                unrestricted_query = qinfo['query'].replace(f"site:{company_website} ", "")
                unrestricted_snippets = google_search(unrestricted_query, qinfo['daterestrict'])
                all_snippets = restricted_snippets + unrestricted_snippets
            else:
                all_snippets = restricted_snippets
        else:
            # No website provided, just do unrestricted search
            all_snippets = google_search(qinfo['query'], qinfo['daterestrict'])
        
        # Generate summary
        if len(all_snippets) == 0:
            sections[section] = f"No information found for {section.replace('_', ' ').title()}."
        else:
            summary = call_llm_with_retry(prompts[section], all_snippets)
            sections[section] = summary
    
    # Deduplicate sections
    sections = deduplicate_sections(sections)
    
    # Format battlecard
    battlecard_content = f"""# {company_name} Battlecard

*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*

## Company Overview
{sections['company_overview']}

## Recent News
{sections['recent_news']}

## Leadership Changes (Past 2 Years)
{sections['leadership_changes']}

## Mergers & Acquisitions (Past 3 Years)
{sections['mergers_acquisitions']}
"""
    
    return {
        'battlecard': battlecard_content,
        'sections': sections
    }

@app.post("/download")
async def download_battlecard(request: BattlecardRequest):
    """
    Download a battlecard as a markdown file.
    
    - **company_name**: The name of the company
    - **company_website**: The company's website domain (optional)
    """
    try:
        company_name = request.company_name.strip()
        company_website = request.company_website.strip() if request.company_website else None
        
        if not company_name:
            raise HTTPException(status_code=400, detail="Please provide a company name")
        
        # Generate battlecard
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, generate_battlecard_sync, company_name, company_website)
        
        # Create file-like object
        file_obj = io.BytesIO(result['battlecard'].encode('utf-8'))
        file_obj.seek(0)
        
        return FileResponse(
            file_obj,
            media_type='text/markdown',
            filename=f"battlecard_{company_name.replace(' ', '_').lower()}.md"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=secure_error_detail(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui():
    """Custom API documentation"""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Battlecard Generator API</title>
        <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui.css" />
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script src="https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui-bundle.js"></script>
        <script>
            window.onload = function() {
                SwaggerUIBundle({
                    url: '/openapi.json',
                    dom_id: '#swagger-ui',
                    presets: [
                        SwaggerUIBundle.presets.apis,
                        SwaggerUIBundle.SwaggerUIStandalonePreset
                    ],
                    layout: "BaseLayout"
                });
            }
        </script>
    </body>
    </html>
    """)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 
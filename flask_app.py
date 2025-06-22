from flask import Flask, render_template, request, jsonify, send_file
import os
import sys
from datetime import datetime
import io
import re

# Add the current directory to Python path to import battlecard_main functions
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import functions from battlecard_main
from battlecard_main import (
    get_queries, get_prompts, google_search, 
    call_llm_with_retry, deduplicate_sections, mask_sensitive_info
)

app = Flask(__name__)

def secure_error_response(error, status_code=500):
    """Return a sanitized error response that doesn't expose sensitive information"""
    error_msg = str(error)
    masked_msg = mask_sensitive_info(error_msg)
    
    # Provide user-friendly error messages
    if "Google Custom Search API" in masked_msg:
        return jsonify({'error': 'Google search service temporarily unavailable. Please try again later.'}), status_code
    elif "Groq LLM API" in masked_msg:
        return jsonify({'error': 'AI processing service temporarily unavailable. Please try again later.'}), status_code
    elif "Missing required environment variables" in masked_msg:
        return jsonify({'error': 'Server configuration error. Please contact administrator.'}), status_code
    else:
        return jsonify({'error': 'An unexpected error occurred. Please try again later.'}), status_code

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_battlecard():
    try:
        data = request.get_json()
        company_name = data.get('company_name', '').strip()
        company_website = data.get('company_website', '').strip()
        
        if not company_name or not company_website:
            return jsonify({'error': 'Please provide both company name and website'}), 400
        
        # Get queries and prompts
        queries = get_queries(company_name, company_website)
        prompts = get_prompts(company_name, company_website)
        sections = {}
        
        # Process each section
        for section, qinfo in queries.items():
            # Search for restricted results
            restricted_snippets = google_search(qinfo['query'], qinfo['daterestrict'])
            
            # Add unrestricted search if needed
            if len(restricted_snippets) > 0 and len(restricted_snippets) < 10:
                unrestricted_query = qinfo['query'].replace(f"site:{company_website} ", "")
                unrestricted_snippets = google_search(unrestricted_query, qinfo['daterestrict'])
                all_snippets = restricted_snippets + unrestricted_snippets
            else:
                all_snippets = restricted_snippets
            
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
        
        return jsonify({
            'success': True,
            'company_name': company_name,
            'battlecard': battlecard_content,
            'sections': sections,
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
    except Exception as e:
        return secure_error_response(e, 500)

@app.route('/download', methods=['POST'])
def download_battlecard():
    try:
        data = request.get_json()
        battlecard_content = data.get('battlecard', '')
        company_name = data.get('company_name', 'company')
        
        # Create file-like object
        file_obj = io.BytesIO(battlecard_content.encode('utf-8'))
        file_obj.seek(0)
        
        return send_file(
            file_obj,
            as_attachment=True,
            download_name=f"battlecard_{company_name.replace(' ', '_').lower()}.md",
            mimetype='text/markdown'
        )
        
    except Exception as e:
        return secure_error_response(e, 500)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 
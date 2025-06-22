import os
import requests
from datetime import datetime
import re
import time

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not installed, continue without it
    pass

# API Configuration - Load from environment variables
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
GOOGLE_API_KEY_2 = os.getenv('GOOGLE_API_KEY_2')
GOOGLE_CSE_ID = os.getenv('GOOGLE_CSE_ID')
GOOGLE_CSE_ID_2 = os.getenv('GOOGLE_CSE_ID_2')
LLM_API_URL = os.getenv('LLM_API_URL', 'https://api.groq.com/openai/v1/chat/completions')
LLM_API_KEY = os.getenv('LLM_API_KEY')

def mask_sensitive_info(text):
    """Mask sensitive information like API keys from error messages"""
    if not text:
        return text
    
    # Mask API keys (common patterns)
    masked = text
    # Google API keys (AIza...)
    masked = re.sub(r'AIza[0-9A-Za-z-_]{35}', '[GOOGLE_API_KEY]', masked)
    # Groq API keys (gsk_...)
    masked = re.sub(r'gsk_[0-9A-Za-z]{32,}', '[GROQ_API_KEY]', masked)
    # CSE IDs - various formats (16-char hex, alphanumeric, etc.)
    masked = re.sub(r'\b[0-9a-f]{16}\b', '[CSE_ID]', masked)  # 16-char hex
    masked = re.sub(r'\b[0-9a-zA-Z]{16,}\b', '[CSE_ID]', masked)  # 16+ char alphanumeric
    # cx parameter specifically
    masked = re.sub(r'cx=[0-9a-zA-Z]{16,}', 'cx=[CSE_ID]', masked)
    # Any other potential API keys
    masked = re.sub(r'Bearer [A-Za-z0-9._-]{20,}', 'Bearer [API_KEY]', masked)
    
    return masked

def secure_raise_error(original_error, context=""):
    """Raise a sanitized error that doesn't expose sensitive information"""
    error_msg = str(original_error)
    masked_msg = mask_sensitive_info(error_msg)
    
    if context:
        masked_msg = f"{context}: {masked_msg}"
    
    # Create a new exception with the masked message
    if isinstance(original_error, requests.exceptions.HTTPError):
        raise requests.exceptions.HTTPError(masked_msg, response=original_error.response)
    elif isinstance(original_error, requests.exceptions.RequestException):
        raise requests.exceptions.RequestException(masked_msg)
    else:
        raise Exception(masked_msg)

# Validate required environment variables
def validate_environment():
    missing_vars = []
    if not GOOGLE_API_KEY:
        missing_vars.append('GOOGLE_API_KEY')
    if not GOOGLE_CSE_ID:
        missing_vars.append('GOOGLE_CSE_ID')
    if not LLM_API_KEY:
        missing_vars.append('LLM_API_KEY')
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set these environment variables in your .env file.")
        print("Make sure your .env file contains the required API keys.")
        return False
    return True

# Search queries for each section
def get_queries(company_name, company_website):
    # daterestrict uses the format 'y[years]', 'm[months]', or 'd[days]'
    return {
        'recent_news': {
            'query': f'"{company_name}" site:{company_website} (news OR press release OR announcement OR product OR expansion OR funding OR partnership OR lawsuit OR legal)',
            'daterestrict': 'y2'
        },
        'leadership_changes': {
            'query': f'"{company_name}" site:{company_website} (press release OR news OR announces OR appoints OR joins OR leaves OR steps down OR resigns OR named OR promoted OR hired OR fired OR leadership change OR CEO OR CFO OR CTO OR executive change OR management change OR board change OR president OR VP) -filetype:pdf',
            'daterestrict': 'y2'
        },
        'mergers_acquisitions': {
            'query': f'"{company_name}" site:{company_website} (merger OR acquisition OR acquired OR acquired by OR M&A OR stake OR equity OR buyout OR merger announcement OR acquisition announcement OR investment OR funding round OR deal closed)',
            'daterestrict': 'y3'
        },
        'company_overview': {
            'query': f'"{company_name}" site:{company_website} (about OR overview OR company profile OR history OR subsidiaries OR parent company OR services OR solutions OR strategic focus OR what we do OR who we are)',
            'daterestrict': None
        }
    }

# Prompts for each section
def get_prompts(company_name, company_website):
    base_warning = "If you are unsure about the accuracy or relevance of a snippet, do not include it. Do not speculate or hallucinate information. Only use reputable news, company, or industry sources. Ignore results from legal case aggregators, unrelated PDFs, or document repositories."
    cluster_instruction = "Cluster similar items together, summarize each cluster, and return the most relevant or representative results for each section."
    return {
        'recent_news': f"""
You are an expert business analyst. Using only the provided web search snippets, og:description, and twitter:description about {company_name} ({company_website}), summarize the most relevant news from the past 2 years. Focus on strategic initiatives, product launches, expansions, funding, partnerships, legal lawsuits, or any news relevant for business development officers. Do not include leadership changes or C-suite appointments or departures in this section. For each news item, provide a 2-3 line summary and include the source link and date. {cluster_instruction} {base_warning} If no information is found, respond with "No recent news found."
""",
        'leadership_changes': f"""
You are an expert business analyst. Using only the provided web search snippets, og:description, and twitter:description about {company_name} ({company_website}), identify C-Suite or leadership changes in the past 2 years. Only include a change if the snippet clearly states a change in an executive role (e.g., CEO, CFO, CTO, President, VP, or any title containing 'Chief'), and the source is a news article, press release, or official company announcement. Ignore snippets from legal documents, court filings, PDFs, or ambiguous mentions. If you are unsure, do not include the item. Do not speculate or hallucinate information. For each change, provide up to 5 bullet points with:
- Name of the individual
- Their new or former title
- Date or approximate time of the change
- A brief 1-3 sentence summary of the context
- The source link
Only include changes within the last 24 months. {cluster_instruction} If no information is found, respond with "No recent leadership changes were found."
""",
        'mergers_acquisitions': f"""
You are an expert business analyst. Using only the provided web search snippets, og:description, and twitter:description about {company_name} ({company_website}), summarize all Mergers and Acquisitions (M&A) involving the company in the past 3 years. Include cases where the company is a buyer, seller, merger partner, interested party, stakeholder, or involved with banks/equity firms. For each, provide up to 5 bullet points with:
- Names of companies involved and their roles
- Date or planned date of the M&A
- 1-3 sentence summary of the outcome
- Date of the citation/source
- The source link
{cluster_instruction} If no information is found, respond with "No recent Merger & Acquisitions found." {base_warning}
""",
        'company_overview': f"""
You are an expert business analyst. Using only the provided web search snippets, og:description, and twitter:description about {company_name} ({company_website}), write a detailed company overview. Include geographical presence, subsidiaries, parent company (if any), history, services and solutions, and strategic focus. Always use citations with dates and provide a source link for each fact. Only use reputable news, company, or industry sources. {cluster_instruction} {base_warning} If information is missing, do not speculate.
"""
    }

def google_search(query, daterestrict=None, num_results=30):
    url = "https://www.googleapis.com/customsearch/v1"
    all_snippets = []
    results_to_fetch = min(num_results, 30)
    for start in range(1, results_to_fetch + 1, 10):
        params = {
            'key': GOOGLE_API_KEY,
            'cx': GOOGLE_CSE_ID,
            'q': query,
            'num': min(10, results_to_fetch - len(all_snippets)),
            'start': start
        }
        if daterestrict:
            params['dateRestrict'] = daterestrict
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429 and GOOGLE_API_KEY_2 and GOOGLE_CSE_ID_2:
                print('Primary Google API key/CSE ID rate limited, retrying with secondary key and CSE ID...')
                params['key'] = GOOGLE_API_KEY_2
                params['cx'] = GOOGLE_CSE_ID_2
                try:
                    response = requests.get(url, params=params)
                    response.raise_for_status()
                except requests.exceptions.HTTPError as e2:
                    secure_raise_error(e2, "Google Custom Search API error (secondary key)")
            else:
                secure_raise_error(e, "Google Custom Search API error")
        except requests.exceptions.RequestException as e:
            secure_raise_error(e, "Google Custom Search API request failed")
        
        data = response.json()
        items = data.get('items', [])
        for item in items:
            metatags = item.get('pagemap', {}).get('metatags', [{}])[0]
            snippet = {
                'title': item.get('title'),
                'snippet': item.get('snippet', ''),
                'og_description': metatags.get('og:description', ''),
                'twitter_description': metatags.get('twitter:description', ''),
                'link': item.get('link'),
                'date': metatags.get('article:published_time', '')
            }
            all_snippets.append(snippet)
        # If we got fewer than 10 results, there are no more pages
        if len(items) < 10:
            break
        if len(all_snippets) >= results_to_fetch:
            break
    return all_snippets

def call_llm(prompt, snippets):
    # Combine snippets, og:description, and twitter:description into a single context
    context = "\n".join([
        f"- {s['title']}: {s['snippet']} {s['og_description']} {s['twitter_description']} (Source: {s['link']}, Date: {s['date']})".strip()
        for s in snippets if any([s['snippet'], s['og_description'], s['twitter_description']])
    ])
    payload = {
        'model': 'llama3-70b-8192',
        'messages': [
            {'role': 'system', 'content': 'You are a helpful assistant.'},
            {'role': 'user', 'content': prompt + "\n\nSnippets:\n" + context}
        ],
        'max_tokens': 1024,
        'temperature': 0.2
    }
    headers = {
        'Authorization': f'Bearer {LLM_API_KEY}',
        'Content-Type': 'application/json'
    }
    try:
        response = requests.post(LLM_API_URL, json=payload, headers=headers)
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        secure_raise_error(e, "Groq LLM API error")
    except requests.exceptions.RequestException as e:
        secure_raise_error(e, "Groq LLM API request failed")
    
    data = response.json()
    return data['choices'][0]['message']['content'].strip()

def call_llm_with_retry(prompt, snippets, retries=3, default_wait=15):
    for attempt in range(retries):
        try:
            return call_llm(prompt, snippets)
        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == 429:
                wait_time = default_wait
                try:
                    # Try JSON first
                    error_json = e.response.json()
                    message = error_json.get('message', '')
                    match = re.search(r'try again in ([0-9.]+)s', message)
                    if match:
                        wait_time = float(match.group(1))
                except Exception:
                    # Try text
                    try:
                        text = e.response.text
                        match = re.search(r'try again in ([0-9.]+)s', text)
                        if match:
                            wait_time = float(match.group(1))
                    except Exception:
                        pass
                print(f"Groq rate limit hit, waiting {wait_time} seconds before retrying...")
                time.sleep(wait_time)
                continue
            # If we get here, it's not a rate limit error, so raise it securely
            secure_raise_error(e, "Groq LLM API error")
        except requests.exceptions.RequestException as e:
            secure_raise_error(e, "Groq LLM API request failed")

def write_battlecard(company_name, sections):
    filename = f"battlecard_{company_name.replace(' ', '_').lower()}.md"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"# {company_name} Battlecard\n\n")
        f.write(f"## Company Overview\n{sections['company_overview']}\n\n")
        f.write(f"## Recent News\n{sections['recent_news']}\n\n")
        f.write(f"## Leadership Changes (Past 2 Years)\n{sections['leadership_changes']}\n\n")
        f.write(f"## Mergers & Acquisitions (Past 3 Years)\n{sections['mergers_acquisitions']}\n")
    return filename

def extract_links(text):
    # Extract all links from a markdown-formatted text
    import re
    return set(re.findall(r'https?://\S+', text))

def deduplicate_sections(sections):
    # Remove overlaps between recent news and leadership changes/mergers_acquisitions
    # Keep items in leadership/mergers, remove from recent news
    news = sections['recent_news']
    leadership = sections['leadership_changes']
    mergers = sections['mergers_acquisitions']

    # Extract links from leadership and mergers
    leadership_links = extract_links(leadership)
    mergers_links = extract_links(mergers)
    all_exclude_links = leadership_links | mergers_links

    # Remove news items that have links in leadership or mergers
    news_lines = news.split('\n')
    filtered_news_lines = []
    for line in news_lines:
        if not any(link in line for link in all_exclude_links):
            filtered_news_lines.append(line)
    filtered_news = '\n'.join(filtered_news_lines)
    sections['recent_news'] = filtered_news
    return sections

def main():
    company_name = input("Enter the company name: ").strip()
    company_website = input("Enter the company website (e.g., example.com): ").strip()
    queries = get_queries(company_name, company_website)
    prompts = get_prompts(company_name, company_website)
    sections = {}
    changes = []
    for section, qinfo in queries.items():
        print(f"Searching for {section.replace('_', ' ').title()} (site restricted)...")
        restricted_snippets = google_search(qinfo['query'], qinfo['daterestrict'])
        print(f"Found {len(restricted_snippets)} restricted results.")
        
        # Only do unrestricted search if we have some restricted results but need more
        if len(restricted_snippets) > 0 and len(restricted_snippets) < 10:
            print(f"Insufficient restricted results for {section.replace('_', ' ').title()}. Adding unrestricted search...")
            unrestricted_query = qinfo['query'].replace(f"site:{company_website} ", "")
            unrestricted_snippets = google_search(unrestricted_query, qinfo['daterestrict'])
            print(f"Found {len(unrestricted_snippets)} additional unrestricted results.")
            # Combine results, prioritizing restricted ones
            all_snippets = restricted_snippets + unrestricted_snippets
        else:
            all_snippets = restricted_snippets
        
        if len(all_snippets) == 0:
            print(f"No results found for {section.replace('_', ' ').title()}, skipping LLM call.")
            sections[section] = f"No information found for {section.replace('_', ' ').title()}."
        else:
            print(f"Found {len(all_snippets)} total snippets. Summarizing...")
            summary = call_llm_with_retry(prompts[section], all_snippets)
            sections[section] = summary
        changes.append(f"{datetime.now().strftime('%Y-%m-%d')}: Added/updated {section.replace('_', ' ').title()} section.")
    # Deduplicate overlaps between sections
    sections = deduplicate_sections(sections)
    battlecard_file = write_battlecard(company_name, sections)
    print(f"Battlecard written to {battlecard_file}")

if __name__ == "__main__":
    if validate_environment():
        main() 
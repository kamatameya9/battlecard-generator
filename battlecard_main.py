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
GOOGLE_API_KEY_3 = os.getenv('GOOGLE_API_KEY_3')
GOOGLE_API_KEY_4 = os.getenv('GOOGLE_API_KEY_4')
GOOGLE_API_KEY_5 = os.getenv('GOOGLE_API_KEY_5')
GOOGLE_CSE_ID = os.getenv('GOOGLE_CSE_ID')
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
def get_queries(company_name, company_website=None):
    # daterestrict uses the format 'y[years]', 'm[months]', or 'd[days]'
    # If company_website is provided, use site-restricted search; otherwise use unrestricted search
    site_restriction = f"site:{company_website} " if company_website else ""
    
    return {
        'recent_news': {
            'query': f'"{company_name}" {site_restriction}(news OR "press release" OR announcement OR product OR expansion OR funding OR \
partnership OR lawsuit OR legal)',
            'daterestrict': 'y2'
        },
        'leadership_changes': {
            'query': f'"{company_name}" {site_restriction} (appoint* OR join* OR resign* OR "steps down" OR retire* OR promot* OR hire* OR name* OR \
"succeeded" OR "replaced" OR "transition" OR succession OR "leadership change" OR "executive change" OR "management change" OR \
CEO OR CFO OR CTO OR COO OR CMO OR CHRO OR CIO OR President OR "Vice President" OR EVP OR SVP OR "Board of Directors" OR "board change")',
            'daterestrict': 'y2'
        },
        'mergers_acquisitions': {
            'query': f'"{company_name}" {site_restriction}("acquisition" OR "acquires" OR "acquired by" OR "merger" OR "merges with" OR "M&A" OR \
"stake purchase" OR "equity investment" OR "strategic investment" OR "joint venture" OR "takeover" OR "sale of business" OR \
"business unit acquisition" OR "spin-off" OR "divestiture" OR "ownership change" OR "buyout" OR "sells subsidiary" OR \
"acquires stake in" OR "enters M&A talks")',
            'daterestrict': 'y3'
        },
        'company_overview': {
            'query': f'"{company_name}" {site_restriction}("company overview" OR "about us" OR "company profile" OR "our history" OR \
"who we are" OR "what we do" OR "subsidiaries" OR "parent company" OR "operates in" OR "headquartered in" OR "global presence" OR \
"services and solutions" OR "strategic focus" OR "business model" OR "core offerings" OR "key markets")',
            'daterestrict': None
        }
    }

# Prompts for each section
def get_prompts(company_name, company_website=None):
    # Create context string for prompts
    company_context = f"{company_name} ({company_website})" if company_website else company_name
    
    return {
        'recent_news': f"""
Using only the provided web search metadata (including title, snippet, og:description, and twitter:description) for {company_context}, \
extract and summarize the most relevant **Recent News** from the past 2 years.

Focus only on business-critical updates, such as:
1. Strategic initiatives or pivots
2. Product launches or enhancements
3. Market expansions or geographic moves
4. Funding rounds (excluding M&A activity)
5. Major partnerships or collaborations
6. Legal issues (lawsuits, regulatory actions)

Instructions:
1. Group similar news items into clusters, summarize each cluster in 2–3 lines.
2. Return only one summary per cluster, selecting the most representative source.
3. Always include the exact source link and publication date of the most representative source with each summary.
4. Only use information from credible news, company, or industry sources.
5. Do not use results from document repositories, PDF aggregators, or irrelevant legal search engines.
6. If the accuracy or relevance of a snippet is unclear, exclude it.
7. Do not speculate or hallucinate. Only use what is clearly present in the snippet metadata.
8. At the end, provide a consolidated bullet-point list of the top 5 recent news items with the publication date and most relevant source links \
(without any subsections or clusters in the final output).

If no valid news is found, respond exactly with:
"No recent news found."
""",
        'leadership_changes': f"""
Using only the provided web search metadata (including title, snippet, og:description, and twitter:description) for {company_context}, \
identify all **C-suite and executive leadership changes** from the past 2 years.

Focus only on the following roles:
1. C-level positions (e.g., CEO, CFO, CTO, COO, CSO, CMO)
2. President, Vice President, Executive Vice President
3. Board-level changes (e.g., chairperson transitions)

Instructions:
1. Group similar or duplicate items into clusters and summarize each cluster once.
2. Return only one summary per cluster, selecting the most representative source.
3. Always include the exact source link and publication date of the most representative source with each summary.
4. Only include information clearly stated in the search metadata. 
5. If a leadership change is uncertain based on the metadata, include it with a clear note about the uncertainty.
6. Do not speculate or hallucinate. Only use what is clearly present in the snippet metadata from reputable sources \
such as credible news, company, or industry publications. Only return results relevant to this company.
7. Ignore results from legal document aggregators, unrelated PDFs, or generic repositories.
8. At the end, for each leadership change, return a **consolidated bullet-point list** with the following details:
  - Name of the individual
  - Their new or former role/title
  - Date or approximate time of the change (be specific if available)
  - A brief 1–3 sentence summary of the context or significance
  - Exact source link

If no relevant leadership changes are found, respond exactly with:
"No recent leadership changes were found."
""",
        'mergers_acquisitions': f"""
Using only the provided web search metadata (including title, snippet, og:description, and twitter:description) for {company_context}, \
identify and summarize all **Mergers & Acquisitions (M&A) activity** from the past 3 years.

Focus only on the transactions where the company acted as:
1. Acquirer or buyer
2. Acquiree or seller
3. Merger participant (announced or completed)
4. Stakeholder in strategic investments, equity deals, or joint ventures
5. Participant in asset or product divestitures/acquisitions (e.g. brands, technology, IP)
6. Engaged party in ownership transitions or restructurings

Instructions:
1. Group similar or duplicate items into clusters and summarize each cluster once.
2. Return only one summary per cluster, selecting the most representative source.
3. Always include the exact source link and publication date of the most representative source with each summary.
4. Only include information clearly stated in the search metadata. 
5. Only include clear and credible M&A events. Do not speculate or infer unconfirmed transactions.
6. Use only reputable news, company, or industry sources. Avoid legal case aggregators, unrelated PDFs, or document repositories.
7. At the end, for each M&A-related item, return a **consolidated bullet-point list** with the following details:
  - Names of all companies involved and their roles (e.g., buyer, seller, target)
  - Date or approximate date of the transaction
  - A brief 1–3 sentence summary describing the deal and its outcome
  - Date of the source
  - Exact source link

If no relevant information is found, respond exactly with: 
"No recent Mergers & Acquisitions found."
""",
        'company_overview': f"""
Using only the provided web search metadata (including title, snippet, og:description, and twitter:description) for {company_context}, \
write a detailed **Company Overview**.

The overview should include key facts about the company's:
1. Geographical presence
2. Subsidiaries (if any)
3. Parent company (if applicable)
4. Brief history or founding background
5. Services, solutions, or key offerings
6. Strategic focus or positioning 

Instructions:
1. If multiple snippets reference similar information, cluster them and use the most relevant/representative.
2. Include exact source links and citation dates for every fact.
3. Use only clearly stated and verifiable facts from reputable news, company, or industry sources.
4. If any detail is uncertain or not mentioned, omit it entirely. Do not speculate or hallucinate.
5. Ignore results from legal case aggregators, unrelated PDFs, AI-generated content, or document repositories.
6. At the end, return a single consolidated paragraph summarizing the commpany overview along with the final bullet point list \
of sources used, with citation dates and URLs. Only show the top 5 most relevant sources.

If no relevant company overview information is found, respond exactly with:
"No reliable company overview information was found."
"""
}

def google_search(query, daterestrict=None, num_results=20, google_api_key=None, google_cse_id=None):
    url = "https://www.googleapis.com/customsearch/v1"
    all_snippets = []
    results_to_fetch = min(num_results, 30)
    # Use provided key or fall back to environment keys (try up to 5 keys)
    api_keys = [
        google_api_key or GOOGLE_API_KEY,
        GOOGLE_API_KEY_2,
        GOOGLE_API_KEY_3,
        GOOGLE_API_KEY_4,
        GOOGLE_API_KEY_5
    ]
    # Remove None/empty keys and deduplicate
    api_keys = [k for k in api_keys if k]
    cse_id = google_cse_id or GOOGLE_CSE_ID
    for start in range(1, results_to_fetch + 1, 10):
        last_exception = None
        for idx, api_key in enumerate(api_keys):
            params = {
                'key': api_key,
                'cx': cse_id,
                'q': query,
                'num': min(10, results_to_fetch - len(all_snippets)),
                'start': start
            }
            if daterestrict:
                params['dateRestrict'] = daterestrict
            try:
                response = requests.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                items = data.get('items', [])
                for item in items:
                    metatags = item.get('pagemap', {}).get('metatags', [{}])[0]
                    snippet = {
                        'title': item.get('title'),
                        'snippet': item.get('snippet', ''),
                        'og_description': metatags.get('og:description', ''),
                        'twitter_description': metatags.get('twitter:description', ''),
                        'link': item.get('link')
                    }
                    all_snippets.append(snippet)
                # If we got fewer than 10 results, there are no more pages
                if len(items) < 10:
                    break
                if len(all_snippets) >= results_to_fetch:
                    break
                last_exception = None
                break  # Success, don't try next keys
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:
                    if idx == len(api_keys) - 1:
                        # Last key, raise error
                        secure_raise_error(e, f"Google Custom Search API error (all {len(api_keys)} keys exhausted)")
                    else:
                        # Try next key
                        last_exception = e
                        continue
                else:
                    secure_raise_error(e, "Google Custom Search API error")
            except requests.exceptions.RequestException as e:
                secure_raise_error(e, "Google Custom Search API request failed")
        if last_exception:
            # If all keys failed, raise the last exception
            secure_raise_error(last_exception, "Google Custom Search API error (all keys failed)")
        # If we got fewer than 10 results, there are no more pages
        if len(all_snippets) >= results_to_fetch:
            break
    return all_snippets

def call_llm(prompt, snippets):
    # Combine snippets, og:description, and twitter:description into a single context
    context = "\n\n".join([
        f"Title: {s['title']}\nSource Link: {s['link']}\nSnippet: {s['snippet']}\nOG Description: {s['og_description']}\n\
Twitter Description: {s['twitter_description']}".strip()
        for s in snippets if any([s['snippet'], s['og_description'], s['twitter_description']])
    ])
    payload = {
        'model': 'llama3-70b-8192',
        'messages': [
            {'role': 'system', 'content': 'You are an expert business analyst.'},
            {'role': 'user', 'content': prompt + "\n\nSnippets:\n" + context}
        ],
        'max_tokens': 8192,
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

def write_battlecard(company_name, sections, filename=None):
    if filename:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"# {company_name} Battlecard\n\n")
            f.write(f"## Company Overview\n{sections['company_overview']}\n\n")
            f.write(f"## Recent News (Past 2 Years)\n{sections['recent_news']}\n\n")
            f.write(f"## Leadership Changes (Past 2 Years)\n{sections['leadership_changes']}\n\n")
            f.write(f"## Mergers & Acquisitions (Past 3 Years)\n{sections['mergers_acquisitions']}\n")
    else:
        filename = f"battlecard_{company_name.replace(' ', '_').lower()}.md"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"# {company_name} Battlecard\n\n")
            f.write(f"## Company Overview\n{sections['company_overview']}\n\n")
            f.write(f"## Recent News (Past 2 Years)\n{sections['recent_news']}\n\n")
            f.write(f"## Leadership Changes (Past 2 Years)\n{sections['leadership_changes']}\n\n")
            f.write(f"## Mergers & Acquisitions (Past 3 Years)\n{sections['mergers_acquisitions']}\n")
    return filename

def llm_deduplicate_sections(sections):
    """
    Use the LLM to deduplicate and reclassify items between sections.
    - Move any items in Recent News that belong in Leadership Changes or M&A to the correct section (if not already present).
    - Remove those items from Recent News.
    - Ensure each item appears only in the most appropriate section.
    """
    prompt = f'''
You are given outputs for four company intelligence sections: Leadership Changes, Mergers & Acquisitions (M&A), Recent News, and Company Overview.

Your task is to:
1. **Deduplicate content across sections**: Remove repeated or overlapping facts. If a fact appears in multiple sections, \
keep it only in the most relevant one. For example, if a leadership appointment appears in both Leadership Changes and Recent News, \
retain it only under Leadership Changes.
2. **Realign misplaced items**: Move facts to the correct section if they are incorrectly categorized. Use the following rules:
   - Leadership Changes: Executive/C-suite role transitions.
   - M&A: Acquisitions, mergers, equity stakes, asset purchases.
   - Company Overview: General profile, history, services, geographic presence.
   - Recent News: Any other significant event not fitting the above.
3. Ensure each item has a **date** and a **reputable source link**. Remove anything lacking a reliable source.
4. Maintain the output structure:
   - Leadership, M&A, and Recent News: bullet points (max 5 per event), each with summary, date, and source link.
   - Company Overview: one clean paragraph with inline citations and source links listed below.

Only include high-quality, non-redundant information. Do not speculate or fabricate. If any section is empty after cleaning, state: \
“No relevant [Section] information found.”

Inputs:
- Leadership Changes: 
{sections['leadership_changes']}

- M&A: 
{sections['mergers_acquisitions']}

- Recent News: 
{sections['recent_news']}

- Company Overview: 
{sections['company_overview']}

Produce:
- Cleaned and realigned sections with no duplication or misplacement, following the above rules.
- Return the cleaned sections in markdown format, using the following template:

## Leadership Changes (Past 2 Years)
[cleaned leadership changes]

## Mergers & Acquisitions (Past 3 Years)
[cleaned M&A]

## Recent News (Past 2 Years)
[cleaned recent news]

## Company Overview
[cleaned company overview]
'''
    # Use the same LLM call as before
    cleaned_markdown = call_llm_with_retry(prompt, [])
    # Parse the markdown back into sections
    import re
    def extract_section(text, header):
        pattern = rf"## {re.escape(header)}\n(.+?)(?=\n## |\Z)"
        match = re.search(pattern, text, re.DOTALL)
        return match.group(1).strip() if match else ""
    return {
        'company_overview': extract_section(cleaned_markdown, "Company Overview"),
        'recent_news': extract_section(cleaned_markdown, "Recent News (Past 2 Years)"),
        'leadership_changes': extract_section(cleaned_markdown, "Leadership Changes (Past 2 Years)"),
        'mergers_acquisitions': extract_section(cleaned_markdown, "Mergers & Acquisitions (Past 3 Years)")
    }

def main():
    company_name = input("Enter the company name: ").strip()
    company_website = input("Enter the company website (optional, press Enter to skip): ").strip()
    
    # Use None if no website provided
    if not company_website:
        company_website = None
        print("No website provided - will use unrestricted search.")
    else:
        print(f"Using site-restricted search for: {company_website}")
    
    queries = get_queries(company_name, company_website)
    prompts = get_prompts(company_name, company_website)
    sections = {}
    changes = []
    
    for section, qinfo in queries.items():
        search_type = "site-restricted" if company_website else "unrestricted"
        print(f"Searching for {section.replace('_', ' ').title()} ({search_type})...")
        
        # If we have a website, try restricted search first, then fallback to unrestricted
        if company_website:
            restricted_snippets = google_search(qinfo['query'], qinfo['daterestrict'])
            print(f"Found {len(restricted_snippets)} restricted results.")
            
            # Only do unrestricted search if we have some restricted results but need more
            if len(restricted_snippets) < 10:
                print(f"Insufficient restricted results for {section.replace('_', ' ').title()}. Adding unrestricted search...")
                unrestricted_query = qinfo['query'].replace(f"site:{company_website} ", "")
                unrestricted_snippets = google_search(unrestricted_query, qinfo['daterestrict'], 20)
                print(f"Found {len(unrestricted_snippets)} additional unrestricted results.")
                # Combine results, prioritizing restricted ones
                all_snippets = restricted_snippets + unrestricted_snippets
            else:
                all_snippets = restricted_snippets
        else:
            # No website provided, just do unrestricted search
            all_snippets = google_search(qinfo['query'], qinfo['daterestrict'])
            print(f"Found {len(all_snippets)} unrestricted results.")
        
        if len(all_snippets) == 0:
            print(f"No results found for {section.replace('_', ' ').title()}, skipping LLM call.")
            sections[section] = f"No information found for {section.replace('_', ' ').title()}."
        else:
            print(f"Found {len(all_snippets)} total snippets. Summarizing...")
            summary = call_llm_with_retry(prompts[section], all_snippets)
            sections[section] = summary
        changes.append(f"{datetime.now().strftime('%Y-%m-%d')}: Added/updated {section.replace('_', ' ').title()} section.")
    
    # Write pre-deduplication battlecard
    pre_file = f"battlecard_{company_name.replace(' ', '_').lower()}_pre_dedup.md"
    write_battlecard(company_name, sections, filename=pre_file)
    print(f"Pre-deduplication battlecard written to {pre_file}")
    
    # Deduplicate overlaps between sections
    deduped_sections = llm_deduplicate_sections(sections)
    post_file = f"battlecard_{company_name.replace(' ', '_').lower()}_post_dedup.md"
    write_battlecard(company_name, deduped_sections, filename=post_file)
    print(f"Post-deduplication battlecard written to {post_file}")

if __name__ == "__main__":
    if validate_environment():
        main() 
# Changelog

## [0.2.0] - 2024-07-09
### Changed
- Fixed LLM API payload to use OpenAI-compatible 'messages' array for Groq endpoint.
- Updated model name to 'llama3-70b-8192' for Groq Llama 3 70B support.

## [0.1.0] - 2024-07-09
### Added
- Initial version: Google Custom Search API integration, LLM summarization, markdown battlecard and run changelog output.

## [0.3.0] - 2024-07-09
### Changed
- Switched to using the 'daterestrict' parameter for Google Custom Search API queries instead of 'after' in the query string.
- Added fallback logic: if a site-restricted search returns fewer than 3 results, the search is retried without restricting to the company website.

## [0.4.0] - 2024-07-09
### Added
- Deduplication logic: removes overlaps between recent news and leadership changes/mergers & acquisitions, keeping items in the latter sections.
- Updated LLM prompts and output to ensure each item in the battlecard includes a source link.

## [0.5.0] - 2024-07-09
### Removed
- All logic related to creating or updating the per-company battlecard changelog file (battlecard_{company_name}_changelog.md). Now only the main battlecard markdown file is generated for each company.

## [0.6.0] - 2024-07-09
### Improved
- Enhanced search queries and LLM prompts to filter out legal case aggregators, unrelated PDFs, and non-news sources.
- Added post-processing to remove items with links to known irrelevant domains from all sections.
- Leadership changes and M&A now require reputable news or company sources for links.

## [0.7.0] - 2024-07-09
### Changed
- Restored company website restriction for the first search iteration in all queries.
- Removed C-suite/leadership keywords from recent news queries and prompts.
- Removed hardcoded site exclusions from queries and deduplication logic.
- Enhanced prompts to instruct the LLM to avoid hallucination, speculation, and to ignore irrelevant sources.

## [0.8.0] - 2024-07-09
### Improved
- Refined leadership changes query to focus on news/press/official language and exclude PDFs by filetype.
- Updated leadership changes prompt to require that the snippet clearly states a change in an executive role and is from a news article, press release, or official company announcement.
- Instructed the LLM to ignore legal documents, court filings, PDFs, or ambiguous mentions, and to not speculate or hallucinate.

## [0.9.0] - 2024-07-09
### Added
- Now fetches up to 50 search results by paginating through the Custom Search API.
- For each result, includes snippet, og:description, and twitter:description in the LLM context.
- Prompts now instruct the LLM to cluster similar items, summarize each cluster, and return the most relevant results.
- Code remains efficient and concise.

## [0.10.0] - 2024-07-09
### Added
- Support for a secondary Google API key. If a 429 rate limit error is encountered with the primary key, the script will automatically retry the request with the secondary key.

## [0.11.0] - 2024-07-09
### Added
- Support for a secondary Google CSE ID. If a 429 rate limit error is encountered, the script will retry the request with both the secondary API key and secondary CSE ID.

## [0.12.0] - 2024-07-09
### Added
- Retry logic for Groq LLM API calls. If a 429 rate limit error is encountered, the script parses the error message for the wait time, sleeps for that duration, and retries up to 3 times before raising the error.

## [0.13.0] - 2024-07-09
### Improved
- Improved Groq LLM API retry logic to always retry on 429 errors, parse wait time from both JSON and text, and fall back to a default wait (15s) if not found. Retries up to 3 times before raising the error.

## [0.14.0] - 2024-07-09
### Changed
- Changed the number of search results fetched per query from 50 to 30 for efficiency and to reduce API usage.

## [0.15.0] - 2024-07-09
### Improved
- Improved search logic to prioritize site-restricted results first, only perform unrestricted search if insufficient restricted results (less than 10), and skip LLM calls when no results are found. Results are combined with restricted ones prioritized.

## [0.16.0] - 2024-07-09
### Improved
- Modified google_search function to stop making unnecessary API calls when no results are returned from a page, improving efficiency and reducing API usage.

## [0.17.0] - 2024-07-09
### Improved
- Enhanced google_search function to stop making API calls when a page returns fewer than 10 results (the maximum per page), indicating no more results are available. This is more efficient than just checking for empty results.

## [0.18.0] - 2024-07-09
### Removed
- Removed redundant check for empty items in google_search function since the len(items) < 10 check already covers both empty results and fewer than 10 results.

## [0.19.0] - 2024-07-09
### Added
- **Streamlit Web App** (`streamlit_app.py`): Complete web interface with modern UI, company input form, progress tracking, and downloadable battlecard results. Features include error handling, loading states, and responsive design.
- **Flask Web App** (`flask_app.py`): Professional web application with HTML templates, RESTful API endpoints, and clean separation of concerns. Includes proper error handling and JSON responses.
- **FastAPI Web App** (`fastapi_app.py`): Modern async API with automatic documentation, request/response models, background task processing, and comprehensive error handling. Features include rate limiting, CORS support, and detailed API documentation.
- **Web Requirements** (`requirements_web.txt`): Separate dependency file for web applications including Streamlit, Flask, FastAPI, and supporting libraries.
- **Web Deployment Guide** (`README_WEB.md`): Comprehensive documentation covering deployment options for all three web implementations including free hosting platforms (Streamlit Cloud, Render, Railway, Vercel, Netlify), environment setup, and troubleshooting guides.
- **HTML Template** (`templates/index.html`): Professional web interface for Flask app with modern styling, form validation, and responsive design.

### Changed
- Updated project structure to support both CLI and web-based usage of the battlecard generator.
- Enhanced documentation to include web deployment instructions and hosting options.

## [0.20.0] - 2024-07-09
### Added
- **Security Improvements**: Removed hardcoded API keys from source code and added proper environment variable validation
- **Environment Setup Helper** (`setup_env.py`): Interactive script to securely set up API keys using `getpass` for hidden input
- **Gitignore Protection** (`.gitignore`): Comprehensive file to exclude sensitive data, environment files, and build artifacts
- **Environment Example** (`env.example`): Template showing required environment variables without exposing actual keys
- **Dotenv Support**: Automatic loading of environment variables from `.env` files with fallback handling

### Changed
- **API Key Handling**: All API keys now loaded from environment variables with validation on startup
- **Error Messages**: Clear error messages when required environment variables are missing
- **Requirements**: Added `python-dotenv` to both `requirements.txt` and `requirements_web.txt`
- **Documentation**: Updated README with comprehensive security instructions and setup options

### Security
- ✅ No hardcoded API keys in source code
- ✅ Environment variable validation prevents runtime errors
- ✅ `.env` files excluded from version control
- ✅ Secure input handling during setup
- ✅ Clear separation of example and actual configuration files

## [0.21.0] - 2024-07-09
### Changed
- **Requirements Consolidation**: Combined `requirements.txt` and `requirements_web.txt` into a single comprehensive requirements file
- **Simplified Setup**: All dependencies (CLI and web) now in one place for easier installation
- **Documentation**: Updated README_WEB.md to reference the unified requirements file

### Removed
- `requirements_web.txt`: Merged into main `requirements.txt` file

## [0.22.0] - 2024-07-09
### Added
- **Secure Error Handling**: Added `mask_sensitive_info()` function to automatically mask API keys from error messages
- **API Key Protection**: All error messages now sanitize sensitive information before being displayed
- **Secure Error Raising**: Added `secure_raise_error()` function to safely propagate errors without exposing secrets

### Security
- ✅ API keys are automatically masked in error messages (AIza... → [GOOGLE_API_KEY])
- ✅ Groq API keys are masked (gsk_... → [GROQ_API_KEY])
- ✅ CSE IDs are masked (16-char hex → [CSE_ID])
- ✅ Bearer tokens are masked (Bearer xxx... → Bearer [API_KEY])
- ✅ All API calls now use secure error handling
- ✅ No sensitive information exposed in client-facing error messages

### Changed
- **Google Search Error Handling**: Updated to use secure error handling with proper fallback logic
- **LLM API Error Handling**: Enhanced to mask API keys in all error scenarios
- **Retry Logic**: Improved to maintain security while handling rate limits 

## [0.23.0] - 2024-07-09
### Added
- **Web App Security**: Added secure error handling to Flask and FastAPI apps to prevent API key exposure
- **Enhanced CSE ID Masking**: Improved CSE ID detection to handle various formats and cx parameter specifically
- **User-Friendly Errors**: Web apps now return generic, user-friendly error messages instead of exposing technical details

### Security
- ✅ Flask app errors now mask sensitive information and return user-friendly messages
- ✅ FastAPI app errors now mask sensitive information and return user-friendly messages
- ✅ CSE ID masking improved to handle 16+ character alphanumeric strings
- ✅ cx parameter specifically masked in error messages
- ✅ All web endpoints now use secure error handling

### Changed
- **Flask Error Handling**: Added `secure_error_response()` function for sanitized error responses
- **FastAPI Error Handling**: Added `secure_error_detail()` function for sanitized error details
- **CSE ID Patterns**: Enhanced regex patterns to catch more CSE ID formats
- **Error Messages**: Replaced technical error details with user-friendly messages 

## [0.24.0] - 2024-07-09
### Added
- **Streamlit Secrets Integration**: Added proper handling of Streamlit Cloud secrets for API key management
- **Debug Information Panel**: Added expandable debug section showing API key status and environment variables
- **Enhanced Error Handling**: Improved error messages with user-friendly descriptions and technical details in expandable sections
- **CSS Styling**: Added comprehensive CSS for better text wrapping and responsive design
- **Environment Validation**: Added pre-execution validation to catch missing API keys early

### Changed
- **Error Message Display**: Replaced long technical error messages with concise, actionable user messages
- **UI/UX Improvements**: Fixed horizontal scrolling issues and improved overall layout
- **Sidebar Configuration**: Set sidebar to always stay expanded and visible
- **Page Configuration**: Added fixed sidebar state and improved page icon handling
- **Error Categorization**: Added specific error handling for 403, 429, and missing environment variables

### Fixed
- **Horizontal Scrolling**: Prevented error messages from causing horizontal overflow
- **Sidebar Collapse**: Fixed sidebar to stay visible and not collapse
- **Text Wrapping**: Ensured all content wraps properly on different screen sizes
- **Streamlit Deployment**: Fixed API key access issues in Streamlit Cloud deployment
- **Error Message Length**: Truncated long error messages to prevent UI overflow

### Security
- ✅ Streamlit secrets properly loaded as environment variables
- ✅ API keys masked in error messages
- ✅ Secure error handling for deployed applications
- ✅ Environment validation before API calls

### UI/UX
- ✅ Fixed sidebar always visible (300px width)
- ✅ Responsive design with proper text wrapping
- ✅ User-friendly error messages with action items
- ✅ Debug information in expandable sections
- ✅ Professional layout with consistent spacing 

## [Unreleased]
### Added
- Support for up to 5 Google API keys (GOOGLE_API_KEY, GOOGLE_API_KEY_2, GOOGLE_API_KEY_3, GOOGLE_API_KEY_4, GOOGLE_API_KEY_5) with automatic rotation in both the backend and the Streamlit web app: the system will try each key in order until one succeeds or all are rate-limited, maximizing available quota.
- Made the company website field optional across all interfaces (CLI, Streamlit, Flask, FastAPI). If not provided, the system now performs unrestricted search across all websites.
- Updated all user interfaces and help messages to clarify that the company website is optional.
- Enhanced fallback logic: when a website is provided but results are insufficient (< 10), automatically adds unrestricted search and combines results, prioritizing site-restricted ones.
- Improved prompts for Recent News and M&A to prevent misclassification of acquisition activities and to specify company roles in M&A.
- Improved leadership changes search and prompts to better capture CEO transitions, interim appointments, and to prevent outdated leadership information in the company overview.
- Enhanced M&A search and prompts to better capture product acquisitions, asset purchases, and to improve deduplication logic.
- Updated FastAPI Pydantic models to make company_website optional.
- Updated all web app forms and validation to only require company name.
- Improved Streamlit layout to prevent page shifting when sidebar is open after content generation.
- Updated Streamlit page icon to a search/research icon.
- Suppressed print statements from imported functions in Streamlit app for a cleaner user experience.
- Removed debug information and API configuration sections from Streamlit app for a cleaner interface.
- Cleaned up output and interface messages for a simpler user flow.
- Improved markdown output formatting and section parsing after LLM deduplication.

### Changed
- Refactored get_queries() and get_prompts() to accept an optional company_website parameter and to apply site restriction at the query level.
- Updated search logic to use site-restricted search first, then fallback to unrestricted when needed (< 10 results).
- Improved error handling and user messages across all interfaces.
- Enhanced deduplication logic to use LLM-powered reclassification, ensuring each item appears only in the most relevant section.
- Improved markdown parsing and output formatting for all sections after LLM deduplication.
- Updated documentation to reflect new optional website behavior and improved user experience.
- Fixed typo in M&A prompt response message ("Merger & Acquisitions" → "Mergers & Acquisitions").

### Technical Details
- Site restriction is now applied at the query level: `site:example.com` if provided, empty string if not.
- Company context in prompts adapts based on whether website is provided.
- Progress messages now show whether search is "site-restricted" or "unrestricted".
- When website is provided but results are insufficient (< 10), automatically adds unrestricted search.
- All existing functionality is preserved when website is provided.
- Removed fixed padding that caused layout shifts in Streamlit, implemented flexible sidebar sizing. 

### Added
- When both default Google API keys are rate-limited in the Streamlit app, the user is now prompted to enter their own Google API key and CSE ID. These credentials are securely stored in the session and used for all subsequent Google search requests, allowing users to continue generating battlecards even after the default quota is exhausted. 
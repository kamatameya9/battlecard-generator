import streamlit as st
import os
import sys
from datetime import datetime
import contextlib
import io

# Add the current directory to Python path to import battlecard_main functions
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set environment variables from Streamlit secrets
if st.secrets:
    os.environ['GOOGLE_API_KEY'] = st.secrets.get('GOOGLE_API_KEY', '')
    os.environ['GOOGLE_API_KEY_2'] = st.secrets.get('GOOGLE_API_KEY_2', '')
    os.environ['GOOGLE_API_KEY_3'] = st.secrets.get('GOOGLE_API_KEY_3', '')
    os.environ['GOOGLE_API_KEY_4'] = st.secrets.get('GOOGLE_API_KEY_4', '')
    os.environ['GOOGLE_API_KEY_5'] = st.secrets.get('GOOGLE_API_KEY_5', '')
    os.environ['GOOGLE_CSE_ID'] = st.secrets.get('GOOGLE_CSE_ID', '')

# Import functions from battlecard_main
from battlecard_main import (
    get_queries, get_prompts, google_search, 
    call_llm_with_retry, llm_deduplicate_sections, validate_environment
)

# Set page config
st.set_page_config(
    page_title="Battlecard Generator",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better layout and text wrapping
st.markdown("""
<style>
    /* Prevent horizontal scrolling */
    .stApp {
        max-width: 100vw;
        overflow-x: hidden;
    }
    
    /* Wrap long error messages and prevent horizontal scrolling */
    .stAlert {
        word-wrap: break-word;
        overflow-wrap: break-word;
        max-width: 100%;
    }
    
    /* Style for error messages */
    .stAlert > div {
        word-break: break-word;
        white-space: pre-wrap;
        max-width: 100%;
    }
    
    /* Make text wrap properly */
    .stMarkdown {
        word-wrap: break-word;
        overflow-wrap: break-word;
        max-width: 100%;
    }
    
    /* Code blocks should also wrap */
    .stCodeBlock {
        word-wrap: break-word;
        overflow-wrap: break-word;
        max-width: 100%;
        overflow-x: auto;
    }
    
    /* Debug info should wrap */
    .streamlit-expanderContent {
        word-wrap: break-word;
        overflow-wrap: break-word;
        max-width: 100%;
    }
    
    /* Responsive sidebar - don't force fixed width */
    .css-1d391kg {
        min-width: 250px !important;
        max-width: 350px !important;
    }
    
    /* Ensure sidebar doesn't collapse but allow flexibility */
    .css-1lcbmhc {
        min-width: 250px !important;
        max-width: 350px !important;
    }
    
    /* Main content area - responsive padding */
    .main .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
        max-width: 100%;
    }
    
    /* When sidebar is present, adjust main content */
    @media (min-width: 768px) {
        .main .block-container {
            padding-left: 2rem;
        }
    }
    
    /* Ensure content doesn't overflow */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: nowrap;
        background-color: transparent;
    }
    
    /* Better spacing for tabs */
    .stTabs [role="tablist"] {
        gap: 2px;
    }
</style>
""", unsafe_allow_html=True)

# Title and description
st.title("🔬 Battlecard Generator")
st.markdown("Generate comprehensive battlecards for any company using AI-powered web search and analysis.")

# Sidebar for inputs
with st.sidebar:
    st.header("Company Information")
    company_name = st.text_input("Company Name", placeholder="e.g., Apple Inc.")
    company_website = st.text_input("Company Website (Optional)", placeholder="e.g., apple.com", help="Leave empty for unrestricted search across all websites")
    
    generate_button = st.button("🚀 Generate Battlecard", type="primary")

# Helper to get Google API keys (up to 5) and CSE ID (from session or env)
def get_google_creds():
    # If user provided their own key, use only that
    if st.session_state.get('user_google_api_key'):
        return [st.session_state['user_google_api_key']], st.session_state.get('user_google_cse_id') or os.getenv('GOOGLE_CSE_ID')
    # Otherwise, collect up to 5 keys from env
    keys = [
        os.getenv('GOOGLE_API_KEY'),
        os.getenv('GOOGLE_API_KEY_2'),
        os.getenv('GOOGLE_API_KEY_3'),
        os.getenv('GOOGLE_API_KEY_4'),
        os.getenv('GOOGLE_API_KEY_5')
    ]
    keys = [k for k in keys if k]
    return keys, os.getenv('GOOGLE_CSE_ID')

# Main content area
if generate_button:
    if not company_name:
        st.error("Please enter a company name.")
    else:
        # Validate environment variables first
        if not validate_environment():
            st.error("❌ Missing required API keys. Please check your Streamlit Cloud settings.")
            st.stop()
        
        # Handle optional company website
        if not company_website:
            company_website = None
        
        # User-provided API key/CSE ID form (shown if needed)
        if st.session_state.get('show_api_form', False):
            st.warning("Default Google API keys have reached their search limit. Please enter your own Google API key and CSE ID to continue.")
            with st.form("api_form"):
                user_api_key = st.text_input("Google API Key", type="password")
                user_cse_id = st.text_input("Google CSE ID", type="password")
                submitted = st.form_submit_button("Save and Retry")
            if submitted:
                if user_api_key and user_cse_id:
                    st.session_state['user_google_api_key'] = user_api_key
                    st.session_state['user_google_cse_id'] = user_cse_id
                    st.session_state['show_api_form'] = False
                    st.rerun()
                else:
                    st.error("Both fields are required.")
            st.stop()
        
        try:
            with st.spinner("Generating battlecard... This may take a few minutes."):
                queries = get_queries(company_name, company_website)
                prompts = get_prompts(company_name, company_website)
                sections = {}
                progress_bar = st.progress(0)
                status_text = st.empty()
                api_keys, cse_id = get_google_creds()
                for i, (section, qinfo) in enumerate(queries.items()):
                    status_text.text(f"Processing {section.replace('_', ' ').title()}...")
                    with contextlib.redirect_stdout(io.StringIO()):
                        # If we have a website, try restricted search first, then fallback to unrestricted
                        if company_website:
                            try:
                                restricted_snippets = google_search(qinfo['query'], qinfo['daterestrict'], google_api_key=api_keys[0] if len(api_keys) == 1 else None, google_cse_id=cse_id)
                            except Exception as e:
                                if '429' in str(e):
                                    st.session_state['show_api_form'] = True
                                    st.rerun()
                                else:
                                    raise
                            if len(restricted_snippets) < 10:
                                status_text.text(f"Adding unrestricted search for {section.replace('_', ' ').title()}...")
                                unrestricted_query = qinfo['query'].replace(f"site:{company_website} ", "")
                                try:
                                    unrestricted_snippets = google_search(unrestricted_query, qinfo['daterestrict'], 20, google_api_key=api_keys[0] if len(api_keys) == 1 else None, google_cse_id=cse_id)
                                except Exception as e:
                                    if '429' in str(e):
                                        st.session_state['show_api_form'] = True
                                        st.rerun()
                                    else:
                                        raise
                                all_snippets = restricted_snippets + unrestricted_snippets
                            else:
                                all_snippets = restricted_snippets
                        else:
                            try:
                                all_snippets = google_search(qinfo['query'], qinfo['daterestrict'], google_api_key=api_keys[0] if len(api_keys) == 1 else None, google_cse_id=cse_id)
                            except Exception as e:
                                if '429' in str(e):
                                    st.session_state['show_api_form'] = True
                                    st.rerun()
                                else:
                                    raise
                        if len(all_snippets) == 0:
                            sections[section] = f"No information found for {section.replace('_', ' ').title()}."
                        else:
                            summary = call_llm_with_retry(prompts[section], all_snippets)
                            sections[section] = summary
                    progress_bar.progress((i + 1) / len(queries))
                sections = llm_deduplicate_sections(sections)
                status_text.text("Battlecard generated successfully!")
                
            # Display results
            st.success(f"✅ Battlecard generated for {company_name}")
            
            # Create tabs for different sections
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "📋 Full Battlecard", 
                "👥 Leadership Changes", 
                "🤝 M&A",
                "📰 Recent News", 
                "🏢 Company Overview"
            ])
            
            with tab1:
                st.markdown(f"# {company_name} Battlecard")
                st.markdown(f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
                
                st.markdown("## Leadership Changes (Past 2 Years)")
                st.markdown(sections['leadership_changes'])

                st.markdown("## Mergers & Acquisitions (Past 3 Years)")
                st.markdown(sections['mergers_acquisitions'])

                st.markdown("## Recent News (Past 2 Years)")
                st.markdown(sections['recent_news'])

                st.markdown("## Company Overview")
                st.markdown(sections['company_overview'])
            
            with tab2:
                st.markdown("## Leadership Changes (Past 2 Years)")
                st.markdown(sections['leadership_changes'])
            
            with tab3:
                st.markdown("## Mergers & Acquisitions (Past 3 Years)")
                st.markdown(sections['mergers_acquisitions'])
            
            with tab4:
                st.markdown("## Recent News (Past 2 Years)")
                st.markdown(sections['recent_news'])
            
            with tab5:
                st.markdown("## Company Overview")
                st.markdown(sections['company_overview'])
            
            # Download button
            battlecard_content = f"""# {company_name} Battlecard

*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*

## Leadership Changes (Past 2 Years)
{sections['leadership_changes']}

## Mergers & Acquisitions (Past 3 Years)
{sections['mergers_acquisitions']}

## Recent News (Past 2 Years)
{sections['recent_news']}

## Company Overview
{sections['company_overview']}
"""
            
            st.download_button(
                label="📥 Download Battlecard",
                data=battlecard_content,
                file_name=f"battlecard_{company_name.replace(' ', '_').lower()}.md",
                mime="text/markdown"
            )
            
        except Exception as e:
            error_msg = str(e)
            
            # Provide user-friendly error messages
            if "Google Custom Search API" in error_msg:
                st.error("❌ Google search service error. Please check your API key and CSE ID in Streamlit Cloud settings.")
            elif "Groq LLM API" in error_msg:
                st.error("❌ AI processing service error. Please check your Groq API key in Streamlit Cloud settings.")
            elif "Missing required environment variables" in error_msg:
                st.error("❌ Missing API keys. Please configure your API keys in Streamlit Cloud settings.")
            elif "403" in error_msg:
                st.error("❌ Access denied. Please verify your API keys are correct and the services are enabled.")
            elif "429" in error_msg:
                st.error("⚠️ Rate limit exceeded. Please wait a moment and try again.")
            else:
                st.error(f"❌ An unexpected error occurred: {error_msg[:100]}{'...' if len(error_msg) > 100 else ''}")
            
            # Show detailed error in expander for debugging
            with st.expander("🔧 Technical Details (for debugging)"):
                st.code(error_msg, language="text")

# Footer
st.markdown("---")

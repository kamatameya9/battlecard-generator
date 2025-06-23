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
    os.environ['GOOGLE_CSE_ID'] = st.secrets.get('GOOGLE_CSE_ID', '')
    os.environ['GOOGLE_CSE_ID_2'] = st.secrets.get('GOOGLE_CSE_ID_2', '')
    os.environ['LLM_API_KEY'] = st.secrets.get('LLM_API_KEY', '')

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
        
        try:
            with st.spinner("Generating battlecard... This may take a few minutes."):
                # Get queries and prompts
                queries = get_queries(company_name, company_website)
                prompts = get_prompts(company_name, company_website)
                sections = {}
                
                # Progress bar
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Process each section with print suppression
                for i, (section, qinfo) in enumerate(queries.items()):
                    status_text.text(f"Processing {section.replace('_', ' ').title()}...")
                    
                    # Suppress print statements from imported functions
                    with contextlib.redirect_stdout(io.StringIO()):
                        # If we have a website, try restricted search first, then fallback to unrestricted
                        if company_website:
                            restricted_snippets = google_search(qinfo['query'], qinfo['daterestrict'])
                            
                            # Only do unrestricted search if we have some restricted results but need more
                            if len(restricted_snippets) > 0 and len(restricted_snippets) < 10:
                                status_text.text(f"Adding unrestricted search for {section.replace('_', ' ').title()}...")
                                unrestricted_query = qinfo['query'].replace(f"site:{company_website} ", "")
                                unrestricted_snippets = google_search(unrestricted_query, qinfo['daterestrict'])
                                # Combine results, prioritizing restricted ones
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
                    
                    # Update progress
                    progress_bar.progress((i + 1) / len(queries))
                
                # Deduplicate sections using LLM-based logic
                sections = llm_deduplicate_sections(sections)
                status_text.text("Battlecard generated successfully!")
                
            # Display results
            st.success(f"✅ Battlecard generated for {company_name}")
            
            # Create tabs for different sections
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "📋 Full Battlecard", 
                "🏢 Company Overview", 
                "📰 Recent News", 
                "👥 Leadership Changes", 
                "🤝 M&A"
            ])
            
            with tab1:
                st.markdown(f"# {company_name} Battlecard")
                st.markdown(f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
                
                st.markdown("## Company Overview")
                st.markdown(sections['company_overview'])
                
                st.markdown("## Recent News")
                st.markdown(sections['recent_news'])
                
                st.markdown("## Leadership Changes (Past 2 Years)")
                st.markdown(sections['leadership_changes'])
                
                st.markdown("## Mergers & Acquisitions (Past 3 Years)")
                st.markdown(sections['mergers_acquisitions'])
            
            with tab2:
                st.markdown("## Company Overview")
                st.markdown(sections['company_overview'])
            
            with tab3:
                st.markdown("## Recent News")
                st.markdown(sections['recent_news'])
            
            with tab4:
                st.markdown("## Leadership Changes (Past 2 Years)")
                st.markdown(sections['leadership_changes'])
            
            with tab5:
                st.markdown("## Mergers & Acquisitions (Past 3 Years)")
                st.markdown(sections['mergers_acquisitions'])
            
            # Download button
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

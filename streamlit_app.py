import streamlit as st
import os
import sys
from datetime import datetime

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
    call_llm_with_retry, deduplicate_sections, validate_environment
)

# Set page config
st.set_page_config(
    page_title="Battlecard Generator",
    page_icon="📊",
    layout="wide"
)

# Title and description
st.title("📊 Battlecard Generator")
st.markdown("Generate comprehensive battlecards for any company using AI-powered web search and analysis.")

# Debug information (only show in development)
if st.secrets:
    with st.expander("🔧 Debug Info (Environment Variables)"):
        st.write("**Google API Key:**", "✅ Set" if st.secrets.get('GOOGLE_API_KEY') else "❌ Not Set")
        st.write("**Google CSE ID:**", "✅ Set" if st.secrets.get('GOOGLE_CSE_ID') else "❌ Not Set")
        st.write("**LLM API Key:**", "✅ Set" if st.secrets.get('LLM_API_KEY') else "❌ Not Set")

# Sidebar for inputs
with st.sidebar:
    st.header("Company Information")
    company_name = st.text_input("Company Name", placeholder="e.g., Apple Inc.")
    company_website = st.text_input("Company Website", placeholder="e.g., apple.com")
    
    # Environment variables setup
    st.header("API Configuration")
    if st.secrets:
        st.success("✅ API keys configured via Streamlit secrets")
    else:
        st.warning("⚠️ API keys not found in Streamlit secrets")
        st.info("Make sure your API keys are set in Streamlit Cloud settings:")
        st.code("""
GOOGLE_API_KEY=your_google_api_key
GOOGLE_API_KEY_2=your_second_google_api_key
GOOGLE_CSE_ID=your_cse_id
GOOGLE_CSE_ID_2=your_second_cse_id
LLM_API_KEY=your_groq_api_key
        """)
    
    generate_button = st.button("🚀 Generate Battlecard", type="primary")

# Main content area
if generate_button:
    if not company_name or not company_website:
        st.error("Please enter both company name and website.")
    else:
        # Validate environment variables first
        if not validate_environment():
            st.error("❌ Missing required API keys. Please check your Streamlit Cloud settings.")
            st.stop()
        
        try:
            with st.spinner("Generating battlecard... This may take a few minutes."):
                # Get queries and prompts
                queries = get_queries(company_name, company_website)
                prompts = get_prompts(company_name, company_website)
                sections = {}
                
                # Progress bar
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Process each section
                for i, (section, qinfo) in enumerate(queries.items()):
                    status_text.text(f"Processing {section.replace('_', ' ').title()}...")
                    
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
                    
                    # Update progress
                    progress_bar.progress((i + 1) / len(queries))
                
                # Deduplicate sections
                sections = deduplicate_sections(sections)
                
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
            st.error(f"An error occurred: {str(e)}")
            st.exception(e)

# Footer
st.markdown("---")
st.markdown("Built with ❤️ using Streamlit, Google Custom Search API, and Groq LLM") 
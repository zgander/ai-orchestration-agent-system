import streamlit as st
from app.services.search_service import GlobalSearchService
from app.models.history_models import SearchResultType

def render_search_page():
    st.title("🔎 Global Repository Search")
    st.write("Search across all cached investigation knowledge (architecture, flows, APIs, chat history, etc.).")
    
    search_service = GlobalSearchService()
    
    # Optional repo filter
    from app.services.investigation_cache import CACHE_DIR
    repo_options = ["All Repositories"]
    if CACHE_DIR.exists():
        repo_options.extend([f.stem for f in CACHE_DIR.glob("*.json")])
        
    col1, col2 = st.columns([3, 1])
    with col1:
        query = st.text_input("Search query...", placeholder="E.g., 'authentication', 'database connection', 'User model'")
    with col2:
        selected_repo = st.selectbox("Filter by Repository", repo_options)
        
    if not query:
        st.info("Enter a search term above to begin.")
        return
        
    repo_filter = None if selected_repo == "All Repositories" else selected_repo
    
    with st.spinner("Searching..."):
        results = search_service.search(query, repo_name=repo_filter)
        
    if not results:
        st.warning("No results found.")
        return
        
    st.success(f"Found {len(results)} results.")
    
    # Filter by type
    types = list(set(r.result_type.value for r in results))
    selected_types = st.multiselect("Filter by Type", types, default=types)
    
    st.divider()
    
    for r in results:
        if r.result_type.value not in selected_types:
            continue
            
        icon = _get_icon_for_type(r.result_type)
        
        with st.container(border=True):
            st.markdown(f"### {icon} {r.title}")
            st.caption(f"Relevance: {r.relevance:.2f} | Section: {r.source_section or 'N/A'}")
            st.markdown(f"> {r.snippet}")
            
            # Action button
            if st.button("View Detail", key=f"btn_{r.title}_{hash(r.snippet)}", help="Not fully hooked up yet."):
                st.info(f"Navigate to {r.url_fragment} is a work in progress.")

def _get_icon_for_type(t: SearchResultType) -> str:
    icons = {
        SearchResultType.FILE: "📄",
        SearchResultType.FOLDER: "📁",
        SearchResultType.SYMBOL: "ƒ",
        SearchResultType.API: "🌐",
        SearchResultType.EXECUTION_FLOW: "🔄",
        SearchResultType.ARCHITECTURE: "🏗️",
        SearchResultType.DOCUMENTATION_GAP: "⚠️",
        SearchResultType.CHAT_HISTORY: "💬",
        SearchResultType.ONBOARDING: "📘"
    }
    return icons.get(t, "🔍")

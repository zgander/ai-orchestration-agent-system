import streamlit as st

def render_dep_graph_page():
    st.title("🕸️ Dependency Graph")
    st.write("Interactive visualization of module dependencies.")
    
    try:
        from streamlit_agraph import agraph, Node, Edge, Config
    except ImportError:
        st.error("Please install streamlit-agraph: `pip install streamlit-agraph`")
        return
        
    if "analysis_result" not in st.session_state:
        st.info("No repository analysis available. Please analyse a repository first.")
        return
        
    analysis = st.session_state.analysis_result
    deps = analysis.dependency_graph
    
    if not deps or not deps.nodes:
        st.info("No dependencies found in this repository.")
        return
        
    nodes = []
    edges = []
    
    # Calculate degrees for sorting
    degrees = {node: 0 for node in deps.nodes}
    for edge in deps.edges:
        if edge.source_file in degrees:
            degrees[edge.source_file] += 1
        if edge.target_file in degrees:
            degrees[edge.target_file] += 1
            
    MAX_NODES = 100
    sorted_nodes = sorted(deps.nodes, key=lambda x: degrees.get(x, 0), reverse=True)
    
    node_map = {}
    for node_id in sorted_nodes[:MAX_NODES]:
        color = "#3b82f6" if node_id.endswith(".py") else "#8b5cf6" if node_id.endswith(".js") else "#10b981"
        
        nodes.append(Node(
            id=node_id,
            label=node_id.split("/")[-1],
            size=25,
            color=color,
            title=node_id
        ))
        node_map[node_id] = True
        
    for edge in deps.edges:
        if edge.source_file in node_map and edge.target_file in node_map:
            edges.append(Edge(
                source=edge.source_file,
                target=edge.target_file,
                color="#9ca3af"
            ))
                
    config = Config(width=800,
                    height=600,
                    directed=True,
                    physics=True,
                    hierarchical=False)

    with st.spinner("Rendering Graph..."):
        return_value = agraph(nodes=nodes, 
                              edges=edges, 
                              config=config)
                              
    if return_value:
        st.write(f"Selected Node: {return_value}")
        
    st.caption(f"Showing {len(nodes)} nodes and {len(edges)} edges. Limited to top {MAX_NODES} modules for performance.")

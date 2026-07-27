from app.analysis.tree_builder import TreeBuilder

def test_tree_builder(sample_repo, mock_settings):
    builder = TreeBuilder(mock_settings)
    tree = builder.analyse(sample_repo)
    
    assert tree.total_files == 3  # main.py, requirements.txt, src/app.py
    assert tree.total_dirs >= 2   # root, src (but not .git because it's ignored)
    assert tree.max_depth == 2    # root (0) -> src (1) -> app.py (2)
    
    # Check that .git is ignored
    git_nodes = [node for node in tree.root.children if node.name == ".git"]
    assert len(git_nodes) == 0
    
    # Check src directory exists
    src_nodes = [node for node in tree.root.children if node.name == "src"]
    assert len(src_nodes) == 1
    
    src_node = src_nodes[0]
    assert src_node.is_dir is True
    assert len(src_node.children) == 1
    assert src_node.children[0].name == "app.py"

from app.analysis.dependency_graph import DependencyGraph

def test_dependency_graph_python(tmp_path, mock_settings):
    # Setup
    app_dir = tmp_path / "app"
    app_dir.mkdir()
    
    (app_dir / "__init__.py").touch()
    
    models = app_dir / "models.py"
    models.write_text("""
class User: pass
""")

    services = app_dir / "services.py"
    services.write_text("""
from app.models import User
import math
""")

    main = tmp_path / "main.py"
    main.write_text("""
from app.services import *
import app.models
""")

    grapher = DependencyGraph(mock_settings)
    graph = grapher.analyse(tmp_path)
    
    nodes = set(graph.nodes)
    assert "app/models.py" in nodes
    assert "app/services.py" in nodes
    assert "main.py" in nodes
    
    edges = graph.edges
    
    # main -> services
    assert any(e.source_file == "main.py" and e.target_file == "app/services.py" for e in edges)
    # main -> models
    assert any(e.source_file == "main.py" and e.target_file == "app/models.py" for e in edges)
    # services -> models
    assert any(e.source_file == "app/services.py" and e.target_file == "app/models.py" for e in edges)


def test_dependency_graph_javascript(tmp_path, mock_settings):
    # Setup
    src = tmp_path / "src"
    src.mkdir()
    
    utils = src / "utils.js"
    utils.write_text("export const add = () => {};")
    
    components = src / "components"
    components.mkdir()
    
    button = components / "Button.jsx"
    button.write_text("""
import React from 'react';
import { add } from '../utils';
""")

    app = src / "App.js"
    app.write_text("""
import Button from './components/Button';
const utils = require('./utils');
""")

    grapher = DependencyGraph(mock_settings)
    graph = grapher.analyse(tmp_path)
    
    edges = graph.edges
    
    # Button -> utils
    assert any(e.source_file == "src/components/Button.jsx" and e.target_file == "src/utils.js" for e in edges)
    
    # App -> Button
    assert any(e.source_file == "src/App.js" and e.target_file == "src/components/Button.jsx" for e in edges)
    
    # App -> utils
    assert any(e.source_file == "src/App.js" and e.target_file == "src/utils.js" for e in edges)

from app.analysis.api_detector import APIDetector

def test_api_detector_python(tmp_path, mock_settings):
    # Setup
    main_py = tmp_path / "main.py"
    main_py.write_text("""
from fastapi import FastAPI

app = FastAPI()

@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id}
    
@router.post("/create")
def create_something():
    pass
""")

    flask_py = tmp_path / "app.py"
    flask_py.write_text("""
from flask import Flask
app = Flask(__name__)

@app.route('/hello', methods=['GET', 'POST'])
def hello_world():
    return 'Hello, World!'
""")

    detector = APIDetector(mock_settings)
    endpoints = detector.analyse(tmp_path)
    
    # Check FastAPI routes
    fastapi_routes = [e for e in endpoints if e.framework == "FastAPI" or e.framework == "Python API"]
    assert len(fastapi_routes) >= 2
    
    get_item = [e for e in fastapi_routes if e.path == "/items/{item_id}"]
    assert len(get_item) == 1
    assert get_item[0].method == "GET"
    assert get_item[0].handler_name == "read_item"
    
    # Check Flask routes
    flask_routes = [e for e in endpoints if e.framework == "Flask"]
    assert len(flask_routes) == 2  # GET and POST
    assert {e.method for e in flask_routes} == {"GET", "POST"}
    assert all(e.path == "/hello" for e in flask_routes)


def test_api_detector_javascript(tmp_path, mock_settings):
    # Setup
    app_js = tmp_path / "app.js"
    app_js.write_text("""
const express = require('express')
const app = express()

app.get('/api/users', (req, res) => {
  res.send('users')
})

router.post("/api/login", function(req, res) {
})
""")

    detector = APIDetector(mock_settings)
    endpoints = detector.analyse(tmp_path)
    
    assert len(endpoints) == 2
    
    get_users = [e for e in endpoints if e.path == "/api/users"]
    assert len(get_users) == 1
    assert get_users[0].method == "GET"
    
    post_login = [e for e in endpoints if e.path == "/api/login"]
    assert len(post_login) == 1
    assert post_login[0].method == "POST"

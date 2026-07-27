import ast
import re

content = """
import sys

def main():
    print("Hello")

if __name__ == '__main__':
    main()
"""

pattern = r"if\s+__name__\s*==\s*['\"]__main__['\"]\s*:"
print("Regex match:", list(re.finditer(pattern, content)))

flask_code = """
from flask import Flask
app = Flask(__name__)

@app.route('/hello', methods=['GET', 'POST'])
def hello_world():
    return 'Hello, World!'
"""

tree = ast.parse(flask_code)
for node in ast.walk(tree):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        print("Function:", node.name)
        for dec in node.decorator_list:
            print("Decorator:", type(dec))
            if isinstance(dec, ast.Call):
                print("Call func type:", type(dec.func))
                if isinstance(dec.func, ast.Attribute):
                    print("Attr:", dec.func.attr)

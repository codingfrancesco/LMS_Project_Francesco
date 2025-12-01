from flask import request, Flask
from markupsafe import escape

app = Flask(__name__)

@app.route("/hello")
def hello():
    name = request.args.get("name", "Flask")
    return f"Hello, {escape(name)}!"
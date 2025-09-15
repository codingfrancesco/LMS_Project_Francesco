from flask import Flask

app = Flask('__Francesco__')
print(__name__)
@app.route("/")
def hello_world():
    return "Hello, bruhh!"


@app.route("/home")
def home():
    return "Hello, home!"

# similar like hello make 9 other pages froms heet
# we will make a route login (/login)

@app.route("/login")
def login():
    return "Login Please"

@app.route("/register")
def register():
    return "Register Please"
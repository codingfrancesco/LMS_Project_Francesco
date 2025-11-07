from flask import Flask, render_template 

app = Flask(__name__)

@app.route("/")
def home():
    return render_template('home.html',)

# we have made  a home.html file and using render template
# we have linked it with home function 

## now also link other link and register with their html you made



@app.route("/login")
def login():
    return render_template('login.html')

@app.route("/register")
def register():
    return render_template('register.html')


@app.route("/lessons")
def lessons():
    return render_template('lessons.html')

@app.route("/course")
def course():
    return render_template('course.html')

@app.route("/assignments")
def assignments():
    return render_template('assignments.html')



app.run(debug=True)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mydatabase.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


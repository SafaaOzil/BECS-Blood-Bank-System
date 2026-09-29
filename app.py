from flask import Flask

from src.models import db


app = Flask(__name__)

# SQLite database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///blood_bank.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Connect SQLAlchemy to the Flask application
db.init_app(app)


# Create database tables
with app.app_context():
    db.create_all()


@app.route("/")
def home():
    return "<h1>BECS - Blood Bank Management System</h1>"


if __name__ == "__main__":
    app.run(debug=True)
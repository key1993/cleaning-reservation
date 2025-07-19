from flask import Flask
from routes import routes
from admin import admin

app = Flask(__name__)
app.register_blueprint(routes)
app.register_blueprint(admin)

if __name__ == "__main__":
    app.run(debug=True)

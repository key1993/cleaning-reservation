from flask import Flask
from routes import routes
from admin import admin
import os


app = Flask(__name__)
app.register_blueprint(routes)
app.register_blueprint(admin)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Render sets PORT env variable
    app.run(host="0.0.0.0", port=port)

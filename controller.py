from flask import Flask,render_template
from applications.config import Config
from applications.db import database

app = Flask(__name__)
app.config.from_object(Config)
database.init_app(app)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
from applications.authorisation import *
from applications.route import *

with app.app_context():
    database.create_all() 




if __name__ == "__main__":
    app.run(port=9999,debug=True)



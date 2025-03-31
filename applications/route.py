from flask import render_template
from controller import app
from applications.db import database
from applications.model import *

@app.route('/')
def index():
    return render_template('a.html')

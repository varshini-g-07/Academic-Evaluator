from flask import Flask
import os
from dotenv import load_dotenv
from flask_pymongo import PyMongo
import secrets
from flask_bootstrap import Bootstrap5
from flask_wtf import CSRFProtect
from flask_login import LoginManager

app = Flask(__name__)

load_dotenv()
app.config['MONGO_URI'] = os.getenv("MONGO_URI")
mongo = PyMongo(app)

foo = secrets.token_urlsafe(16)
app.secret_key = foo

bootstrap = Bootstrap5(app)
csrf = CSRFProtect(app)

login = LoginManager()
login.init_app(app)
login.login_view = 'teacherLogin'

from app import routes
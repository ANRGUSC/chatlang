from flask import Flask
from flask import Blueprint
import os
import dotenv
from werkzeug.middleware.proxy_fix import ProxyFix
import pathlib

thisdir = pathlib.Path(__file__).parent

dotenv.load_dotenv()
if os.getenv('FLASK_ENV') != 'production' and thisdir.joinpath('dev.env').exists():
    dotenv.load_dotenv('dev.env', verbose=True, override=True)

PREFIX = os.getenv('PREFIX')

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_host=1, x_proto=1)  # Adjust these values according to your setup
bp = Blueprint('chatlang', __name__, url_prefix=PREFIX, static_folder='static', static_url_path='/static')

from flask import Flask
from flask import Blueprint
import os
import dotenv
from werkzeug.middleware.proxy_fix import ProxyFix


dotenv.load_dotenv()

PREFIX = os.getenv('PREFIX')


app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_host=1, x_proto=1)  # Adjust these values according to your setup
bp = Blueprint('chatlang', __name__, url_prefix=PREFIX, static_folder='static', static_url_path='/static')

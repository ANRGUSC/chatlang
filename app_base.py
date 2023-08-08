from flask import Flask
from flask import Blueprint
import os
import dotenv

dotenv.load_dotenv()

PREFIX = os.getenv('PREFIX')


app = Flask(__name__)
bp = Blueprint('chatlang', __name__, url_prefix=PREFIX, static_folder='static', static_url_path='/static')

import coloredlogs, os, redis
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import logging
import asyncio
import json
from time import time

import configure
from app import *

if __name__ == "__main__":
    app.run(host=configure.FLASK.HOST, 
            port=configure.FLASK.PORT, 
            use_reloader=False , 
            debug=configure.FLASK.DEBUG)
    

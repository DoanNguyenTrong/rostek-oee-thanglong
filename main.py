import logging
from configure import  *
from app import *

if __name__ == "__main__":
    app.run(host=FLASK.HOST, port=FLASK.PORT, use_reloader=False , debug=FLASK.DEBUG)


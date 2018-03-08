#!flask/bin/python
# C:\Users\joogl\PycharmProjects\Py3_Asyncio_RestPing
from flask import Flask, jsonify
import logging
import http.client

#---------------------------------#
app = Flask(__name__)
# app.logger.addHandler(handler)

tasks = [
    {
        'id': 1,
        'title': u'Buy',
        'description': u'Tuples of securities with prices',
        'done': False
    },
    {
        'id': 2,
        'title': u'Sell',
        'description': u'Tuples of securities with prices',
        'done': False
    },
    {
        'id': 3,
        'title': u'Bookings',
        'description': u'Tuples of securities with power imbalances',
        'done': False
    }
]

counter = 1
# ---------------------------------#

@app.route("/")
def request_count():
    global counter
    counter += 1
    return str(counter)

# ---------------------------------#
@app.route('/todo/api/v1.0/tasks', methods=['GET'])
def get_tasks():
    global counter
    counter += 1
    return jsonify({'tasks': tasks, 'count': str(counter)})

# ---------------------------------#

if __name__ == '__main__':
    # ---------------------------------#
    """
    # logger = logging.getLogger('werkzeug')
    # handler = logging.FileHandler('access.log')
    # logger.addHandler(handler)
    http.client.HTTPConnection.debuglevel = 1
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True
    """
    # ---------------------------------#
    logFormatStr = '[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s'
    logging.basicConfig(format=logFormatStr, filename="global.log", level=logging.DEBUG)
    formatter = logging.Formatter(logFormatStr, '%m-%d %H:%M:%S')
    fileHandler = logging.FileHandler("summary.log")
    fileHandler.setLevel(logging.DEBUG)
    fileHandler.setFormatter(formatter)
    streamHandler = logging.StreamHandler()
    streamHandler.setLevel(logging.DEBUG)
    streamHandler.setFormatter(formatter)
    app.logger.addHandler(fileHandler)
    app.logger.addHandler(streamHandler)
    app.logger.info("Logging is set up.")

    app.run(debug=True, threaded=True)
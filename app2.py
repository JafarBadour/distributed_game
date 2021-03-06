from flask import Flask, jsonify, make_response
from celery_spawner import make_celery
from flask_cors import CORS

import redis

flask_app = Flask(__name__)
CORS(flask_app)


flask_app.config.update(
    CELERY_BROKER_URL='redis://localhost:6379',
    CELERY_RESULT_BACKEND='redis://localhost:6379'
)
celery = make_celery(flask_app)

r = redis.Redis(host='localhost', port=6379)


def active():
    pass


import json


@celery.task(name='app.updstate')
def updstate(new_state, key='newstate'):
    db = json.loads(r.get(key).decode().replace("\'", "\""))
    db.update(new_state)

    r.mset({key: str(db)})
    return db


@celery.task(name='app.getstate')
def getstate(key='newstate'):
    print(r.get(key), 'getstate')

    return json.loads(r.get(key).decode().replace("\'", "\""))


@flask_app.route('/update_state/<state>', methods=['GET'])
def update_state(state):
    obj = updstate.delay(state)

    return 'Ok'


@flask_app.route('/get_state/', methods=['GET'])
def get_state():
    return str(r.mget('newstate')[0].decode())  # .decode()


@flask_app.route('/login/', methods=['GET'])
def login():
    db = getstate.delay()
    db = db.get()
    print(db)
    colors = ['red', 'green', 'yellow', 'blue']
    import random
    for r in colors:

        if any(o == r for o in db.keys()):
            continue
        from datetime import datetime
        db.update({r: {
            "piece1": 126,
            "piece2": 129,
            "lastseen": datetime.utcnow().strftime("%H-%M-%S"),
            "turn": len(db.keys()),
        }})
        resp = jsonify(db)
        updstate.delay(db)

        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp
    return make_response("Error no seats in the game")


@flask_app.route('/reset/', methods=['GET'])
def reset():
    r.mset({'newstate' : b'{}'} )
    return 'Ok'

if __name__ == '__main__':
    updstate.delay({})
    while True:
        try:
            import random

            flask_app.run(debug=True, host='0.0.0.0', port=5001)  # random.randint(1,1<<15))
            break
        except:
            continue

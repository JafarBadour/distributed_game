from flask import Flask, jsonify, make_response, request
from celery_spawner import make_celery
from flask_cors import CORS
from datetime import datetime
import redis

flask_app = Flask(__name__)
piece1_dict = {
    'red': 41,
    'green': 47,
    'yellow': 45,
    'blue': 43
}
cols = ['red', 'green', 'yellow', 'blue']

piece2_dict = {
    'red': 42,
    'green': 48,
    'yellow': 46,
    'blue': 44
}
flask_app.config.update(
    CELERY_BROKER_URL='redis://localhost:6379',
    CELERY_RESULT_BACKEND='redis://localhost:6379'
)
celery = make_celery(flask_app)

r = redis.Redis(host='localhost', port=6379)


def active():
    tdate = get_time_turn_date()
    res = []
    for col in cols:
        if tdate[col] > 20:
            continue
        res.append(col)
    return res


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


@flask_app.route('/update_state/', methods=['POST'])
def update_state():
    print(request.data)
    state = json.loads(request.data.decode())
    print(state, 'post req')
    col = state['color']
    state[col]['lastseen'] = datetime.utcnow().strftime("%H-%M-%S")
    actv = active()
    for col in cols:
        state[col]["turn"] = (state[col]["turn"] + 1) % 4
    for col in cols:
        if col in actv:
            continue
        if state[col]["turn"] != 0:
            continue
        for col in cols:
            state[col]["turn"] = (state[col]["turn"] + 1) % 4

    obj = updstate.delay(state)

    resp = make_response('Ok')
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp


def won(col, resp):
    conditions = {
        'red': 1,
        'green': 25,
        'yellow': 17,
        'blue': 9
    }
    return resp[col]['piece1'] == conditions[col] and resp[col]['piece2'] == conditions[col]


def get_time_turn_date():
    resp = getstate.delay()
    resp = resp.get()
    now = datetime.utcnow()
    result = {"turn": {}}
    for col in cols:
        result[col] = (now - datetime.strptime(resp[col]['lastseen'], "%H-%M-%S")).seconds
    return result


@flask_app.route('/get_timers/<color>', methods=['GET'])
def get_timers(color):
    resp = getstate.delay()
    resp = resp.get()
    now = datetime.utcnow()
    result = {"turn": {}}
    for col in cols:
        result[col] = (now - datetime.strptime(resp[col]['lastseen'], "%H-%M-%S")).seconds
        result[col] = str(result[col]) + (" (Dead)" if result[col] > 20 else " (Alive)")
    turn, tmin = '', 5
    for col in active():
        if resp[col]["turn"] < tmin:
            turn = col
            tmin = resp[col]["turn"]

    result["turn"] = turn
    actv = active()
    if len(actv) == 1:
        result["turn"] = actv[0] + " Won wohoo"
    else:
        for col in actv:
            if won(col, resp):
                result["turn"] = col + " Won wohoo"
    resp = jsonify(result)

    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp


@flask_app.route('/get_state/<color>', methods=['GET'])
def get_state(color):
    resp = getstate.delay()
    resp = resp.get()
    try:
        resp[color]['lastseen'] = datetime.utcnow().strftime("%H-%M-%S")
        updstate.delay(resp)
    except:
        pass
    resp = jsonify(resp)

    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp


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
            "piece1": piece1_dict[r],
            "piece2": piece2_dict[r],
            "lastseen": datetime.utcnow().strftime("%H-%M-%S"),
            "turn": len(db.keys()),
        }})
        resp = jsonify(db)
        updstate.delay(db)

        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp
    resp = make_response("Error no seats in the game")
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp


@flask_app.route('/reset/', methods=['GET'])
def reset():
    r.mset({'newstate': b'{}'})
    resp = make_response('Ok')
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp


if __name__ == '__main__':
    CORS(flask_app, origins=['0.0.0.0:5000'])
    updstate.delay({})
    while True:
        try:
            import random

            flask_app.run(debug=True, host='0.0.0.0', port=5000)  # random.randint(1,1<<15))
            break
        except:
            continue

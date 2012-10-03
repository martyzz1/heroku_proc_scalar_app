import os
#test
import time
import math
import heroku
import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app import App

DATABASE_URL = os.environ.get('DATABASE_URL', False)
SLEEP_PERIOD = os.environ.get('SLEEP_PERIOD', 10)
COUNT_BOUNDARY = os.environ.get('COUNT_BOUNDARY', 0)
HEROKU_API_KEY = os.environ.get('HEROKU_API_KEY', False)

assert(DATABASE_URL)
assert(HEROKU_API_KEY)

print "[worker] ini using COUNT_BOUNDARY=%s" % COUNT_BOUNDARY
print "[worker] ini using DATABASE_URL=%s" % DATABASE_URL
print "[worker] ini using SLEEP_PERIOD=%s" % SLEEP_PERIOD
print "[worker] ini using HEROKU_API_KEY=%s" % HEROKU_API_KEY


def _get_database():

    engine = create_engine(DATABASE_URL)

    return engine


def process_apps(app, heroku_conn):

    data = get_data(app)
    if not data:
        return

    for procname, count in data:
        if procname not in heroku_conn.apps:
            print "[ERROR] %s is not available via your configured HEROKU_API %s" % (app.appname, HEROKU_API_KEY)
        else:
            heroku_app = heroku_conn.apps[app.appname]
            new_process_count = check_for_scaling(heroku_app, count)
            if not new_process_count:
                break
            else:
                print "Scaling %s dyno process %s to %d" % (app.appname, procname, new_process_count)
                scale_dyno(heroku_app, procname, new_process_count)


def scale_dyno(heroku_app, procname, count):
    heroku_app.processes[procname].scale(count)


def get_current_dynos(heroku_app):
    web_proc = heroku_app.processes['web']
    cpt = 0
    for proc in web_proc:
        cpt += 1

    return cpt


def check_for_scaling(heroku_app, count):
    required_count = calculate_required_dynos(count)
    current_dyno_count = int(get_current_dynos(heroku_app))

    if not current_dyno_count == required_count:
        scale_dyno(heroku_app, required_count)


def calculate_required_dynos(count):

    if COUNT_BOUNDARY == 0:
        if count > 0:
            return 1
        else:
            return 0
    else:
        if count > 0:
            return math.ceil(float(count) / float(COUNT_BOUNDARY))
        else:
            return 0


def get_data(app):

    r = ''
    if app.username or app.password:
        r = requests.get(app.app_api_url, auth=(app.user, app.password))
        if not r.status_code == 200:
            print "[ERROR] %s call to %s with user = %s and password = %s Returned response code %s and the following message" % (app.appname, app.app_api_url, app.username, app.password, r.status_code)
            print r.text
            return
    else:
        r = requests.get(app.app_api_url)
        if not r.status_code == 200:
            print "[ERROR] %s call to %s without user or password Returned response code %s and the following message" % (app.appname, app.app_api_url, r.status_code)
            print r.text
            return

    return r.json


engine = _get_database()
Session = sessionmaker(bind=engine)
while(True):
    print "==============================================================================="
    session = Session()
    apps = session.query(App).all()
    heroku_conn = heroku.from_key(HEROKU_API_KEY)
    for app in apps:
        process_apps(app, heroku_conn)
    print "sleeping for %f" % SLEEP_PERIOD
    time.sleep(SLEEP_PERIOD)

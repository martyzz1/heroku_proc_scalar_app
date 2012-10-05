import os
#test
import time
import math
import heroku
import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app import App
from pprint import pprint

DATABASE_URL = os.environ.get('DATABASE_URL', False)
SLEEP_PERIOD = os.environ.get('SLEEP_PERIOD', 10)
COUNT_BOUNDARY = os.environ.get('COUNT_BOUNDARY', 0)
HEROKU_API_KEY = os.environ.get('HEROKU_API_KEY', False)

assert(DATABASE_URL)
assert(HEROKU_API_KEY)

print "[INIT] using COUNT_BOUNDARY=%s" % COUNT_BOUNDARY
print "[INIT] using DATABASE_URL=%s" % DATABASE_URL
print "[INIT] using SLEEP_PERIOD=%s" % SLEEP_PERIOD
print "[INIT] using HEROKU_API_KEY=%s" % HEROKU_API_KEY


def _get_database():

    engine = create_engine(DATABASE_URL)

    return engine


def process_apps(app, heroku_conn):

    data = get_data(app)
    pprint(data)
    if not data:
        return

    for procname, info in data.iteritems():
        count = info['count']
        active_count = info['active']
        try:
            heroku_app = heroku_conn.apps[app.appname]
        except KeyError:
            print "[ERROR] %s is not available via your configured HEROKU_API %s" % (app.appname, HEROKU_API_KEY)
            pprint(heroku_conn.apps)
            pprint(heroku_conn.apps[app.appname])
        else:
            print "\n\n[%s] Checking for scaling on %s" % (app.appname, procname)
            check_for_scaling(heroku_conn, heroku_app, app, procname, count, active_count)


def scale_dyno(heroku_conn, heroku_app, app, procname, count):
    appname = app.appname

    if count == 0:
        #we need to call the shutdown control_app
        shutdown_app(heroku_conn, app, procname)
    else:
        try:
            heroku_app.processes[procname].scale(count)
        except KeyError:
            #this means the prc isn't running - bug in heroku api methinks
            # see http://samos-it.com/only-use-worker-when-required-on-heroku-with-djangopython/
            heroku_conn._http_resource(method='POST', resource=('apps', appname, 'ps', 'scale'), data={'type': procname, 'qty': count})


def shutdown_app(heroku_conn, app, procname):

    heroku_app = heroku_conn.apps[app.appname]
    print "[%s] shutting down processes %s" % (app.appname, procname)
    heroku_app.run_sync("fab shutdown_celery_process:%s" % procname)
    #is it already running?
    #if get_current_dynos(heroku_app, control_app):
        #print "[%s]  WARN - control_app is already in the process of shutting down processes, doing nothing" % app.appname
    #else:
        #start the control_app
        #print "[%s] starting control_app %s to shutdown processes" % (app.appname, control_app)
        #scale_dyno(heroku_conn, heroku_app, app, control_app, 1)


def get_current_dynos(heroku_app, procname):
    try:
        web_proc = heroku_app.processes[procname]
    except KeyError:
        return 0
    else:
        cpt = 0
        for proc in web_proc:
            cpt += 1

        return cpt


def check_for_scaling(heroku_conn, heroku_app, app, procname, count, active_tasks):
    appname = app.appname

    required_count = calculate_required_dynos(count)
    current_dyno_count = int(get_current_dynos(heroku_app, procname))

    print "[%s] current task count for %s = %s" % (appname, procname, count)
    print "[%s] current_dyno_count for %s = %s" % (appname, procname, current_dyno_count)

    if not current_dyno_count == required_count:
        print "[%s] Scaling dyno process %s to %d" % (appname, procname, required_count)
        if required_count == 0 and active_tasks > 0:
            print "[%s] Not Scaling %s dyno to 0 yet as it still has %s active tasks" % (appname, procname, active_tasks)
        else:
            scale_dyno(heroku_conn, heroku_app, app, procname, required_count)


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
    print "[INFO] sleeping for %f" % SLEEP_PERIOD
    time.sleep(SLEEP_PERIOD)

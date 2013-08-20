import os
import irc
import time
import math
import heroku
import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from schema import App
from pprint import pprint

DATABASE_URL = os.environ.get('DATABASE_URL', False)
SLEEP_PERIOD = float(os.environ.get('SLEEP_PERIOD', 10))
HEROKU_API_KEY = os.environ.get('HEROKU_API_KEY', False)
NOTIFICATIONS = os.environ.get('NOTIFICATIONS', False)

max_str_length = 180

assert(DATABASE_URL)
assert(HEROKU_API_KEY)

print "[INIT] using DATABASE_URL=%s" % DATABASE_URL
print "[INIT] using SLEEP_PERIOD=%s" % SLEEP_PERIOD
print "[INIT] using HEROKU_API_KEY=%s" % HEROKU_API_KEY


def process_apps(app, heroku_conn):
    data = get_data(app)
    if not data:
        return

    for procname in data.iterkeys():
        count = data[procname]['count']
        active_count = data[procname]['active']
        if 'deploy_lock' in data[procname] and data[procname]['deploy_lock'] != 0:
            print "[%s] %s is locked for %s, skipping".ljust(max_str_length) % (app.appname, procname, data[procname]['deploy_lock'])
            continue
        try:
            heroku_app = heroku_conn.apps[app.appname]
        except KeyError:
            print "\n[ERROR] %s is not available via your configured HEROKU_API %s.\nAvailable apps are:-\n" % (app.appname, HEROKU_API_KEY)
            pprint(heroku_conn.apps)
        else:
            print "[%s] Checking for scaling on %s".ljust(max_str_length) % (app.appname, procname)
            check_for_scaling(heroku_conn, heroku_app, app, procname, count, active_count)


def scale_dyno(heroku_conn, heroku_app, app, procname, count):
    appname = app.appname

    if count == 0:
        # we need to call the shutdown control_app
        shutdown_app(heroku_conn, app, procname)
    else:
        if NOTIFICATIONS:
            irc.send_irc_message("[%s] Scaling %s processes to %s" % (appname, procname, count))
        try:
            heroku_app.processes[procname].scale(count)
        except KeyError:
            # this means the proc isn't running - bug in heroku api methinks
            # see http://samos-it.com/only-use-worker-when-required-on-heroku-with-djangopython/
            heroku_conn._http_resource(method='POST', resource=('apps', appname, 'ps', 'scale'), data={'type': procname, 'qty': count})


def shutdown_app(heroku_conn, app, procname):

    heroku_app = heroku_conn.apps[app.appname]
    running_already = 0
    cmd = "fab shutdown_celery_process:%s" % procname
    try:
        web_proc = heroku_app.processes['run']
    except KeyError:
        running_already = 0
    else:
        print "possibly got running process, checking for %s".ljust(max_str_length) % cmd
        for proc in web_proc:
            if proc.command == cmd:
                running_already = 1

    if running_already == 1:
        print "[%s] Shutdown command for %s already running... skipping....".ljust(max_str_length) % (app.appname, procname)
    else:
        print "[%s] shutting down processes %s".ljust(max_str_length) % (app.appname, procname)
        if NOTIFICATIONS:
            irc.send_irc_message("[%s] shutting down processes %s" % (app.appname, procname))
        pprint(heroku_app)
        heroku_conn._http_resource(method='POST', resource=('apps', app.appname, 'ps'), data={'command': cmd})


def get_current_dynos(heroku_conn, heroku_app, app, procname):
    try:
        web_proc = heroku_app.processes[procname]
    except KeyError:
        return 0
    else:

        cpt = 0
        for proc in web_proc:
            if proc.state == 'crashed':
                print "%s is crashed - Scaling it down" % procname
                scale_dyno(heroku_conn, heroku_app, app, procname, 0)
            cpt += 1

        return cpt


def check_for_scaling(heroku_conn, heroku_app, app, procname, count, active_tasks):
    appname = app.appname
    max_dynos = int(app.max_dynos)
    min_dynos = int(app.min_dynos)

    required_count = calculate_required_dynos(count, max_dynos, min_dynos, int(app.count_boundary))
    current_dyno_count = int(get_current_dynos(heroku_conn, heroku_app, app, procname))

    print "[%s] %s has %s running dynos and %s pending tasks".ljust(max_str_length) % (appname, procname, current_dyno_count, count)

    if not current_dyno_count == required_count:
        print "[%s] Scaling %s dyno process to %d".ljust(max_str_length) % (appname, procname, required_count)
        if required_count == 0 and active_tasks > 0:
            print "[%s] Not shutting down %s dyno yet as it still has %s active tasks".ljust(max_str_length) % (appname, procname, active_tasks)
        else:
            scale_dyno(heroku_conn, heroku_app, app, procname, required_count)


def calculate_required_dynos(count, max_dynos, min_dynos, count_boundary):

    if count_boundary == 0:
        if count > 0:
            return 1
        else:
            if count <= min_dynos:
                # print "Min dynos reached"
                return min_dynos
            else:
                return 0
    else:
        if count > 0:
            calc = math.ceil(float(count) / float(count_boundary))
            if calc >= max_dynos:
                # print "Max dynos reached"
                return max_dynos
            else:
                return calc
        else:
            if count <= min_dynos:
                # print "Min dynos reached"
                return min_dynos
            else:
                return 0


def get_data(app):
    if app.username or app.password:
        # print "[%s]Loading data, using authentication method please wait..... %s ".ljust(max_str_length) % (app.appname, app.app_api_url)
        try:
            r = requests.get(app.app_api_url, auth=(app.username, app.password), timeout=10.0)
        except Exception, e:
            print "\n[Error] %s for %s" % (e, app.app_api_url)
            return

        if not r.status_code == 200:
            print "\n[ERROR] %s call to %s with user = %s and password = %s Returned response code %s and the following message" % (
                    app.appname, app.app_api_url, app.username, app.password, r.status_code)
            #print r.text
            return
    else:
        # print "[%s]Loading data, please wait.....".ljust(max_str_length) % app.appname
        try:
            r = requests.get(app.app_api_url)
        except Exception, e:
            print "\n[Error] %s for %s" % (e, app.app_api_url)
            return
        if not r.status_code == 200:
            print "[ERROR] %s call to %s without user or password Returned response code %s and the following message" % (
                    app.appname, app.app_api_url, r.status_code)
            return

    return r.json


engine = create_engine(DATABASE_URL)
Session = scoped_session(sessionmaker(bind=engine))
while(True):
    print "\n\n====================[Beginning Run]=======================\n".ljust(max_str_length)
    session = Session()
    apps = session.query(App).order_by("app_appname").all()
    heroku_conn = heroku.from_key(HEROKU_API_KEY)
    print("rate_limit_remaining = {0}".format(heroku_conn.ratelimit_remaining()))
    #newapp = heroku_conn.create_app(name='martyzz1test', stack='cedar', region_name='us')
    #pprint(newapp)
    #pprint(newapp.addons)
    app = heroku_conn.app('martinsharehoodadmin')
    for addon in app.addons:
        print addon.app.name, " - ", addon.plan.name

    app = heroku_conn.app('martyzz1test')
    for addon in app.addons:
        print addon.app.name, " - ", addon.plan.name

    addons = heroku_conn.addon_services
    pprint(addons)

    pg_addon = heroku_conn.addon_services('heroku-postgresql:basic')
    pprint(pg_addon)

    app.install_addon(plan_name='heroku-postgresql:basic')
    for addon in app.addons:
        print addon.app.name, " - ", addon.plan.name

    assert(False)
    print("rate_limit_remaining = {0}".format(heroku_conn.ratelimit_remaining()))
    pprint(app.addons)
    app2 = heroku_conn.apps['martinsharehoodadmin']
    print("rate_limit_remaining = {0}".format(heroku_conn.ratelimit_remaining()))
    pprint(app2.addons)
    print("rate_limit_remaining = {0}".format(heroku_conn.ratelimit_remaining()))
    #rate_limits = heroku_conn.addons
    #pprint(rate_limits)
    for app in apps:
        process_apps(app, heroku_conn)
        time.sleep(3)
    print "Cycle Complete sleeping for %f".ljust(max_str_length) % SLEEP_PERIOD
    time.sleep(SLEEP_PERIOD)

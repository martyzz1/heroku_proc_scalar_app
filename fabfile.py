import heroku
import os
from pprint import pprint # NOQA
from urlparse import urlparse
from fabric.api import task, abort
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from proc_scalar.schema import App


@task
def set_max_dynos(appname, num):
    return update_app(appname, {'max_dynos': num})


@task
def set_min_dynos(appname, num):
    return update_app(appname, {'min_dynos': num})


@task
def set_api_key(appname, key):
    return update_app(appname, {'api_key': key})


def update_app(appname, settings):
    engine = _get_database()
    Session = sessionmaker(bind=engine)
    session = Session()

    app = session.query(App).filter_by(appname=appname).first()

    if app is None:
        abort("App {0:s} doesn't exist".format(appname))

    for key in settings.iterkeys():
        setattr(app, key, settings[key])

    session.commit()


@task
def add_app(appname, app_api_url=False, min_dynos=0, max_dynos=5, count_boundary=0):

    """heroku run fab add_app:martinsharehoodadmin,"https://user:pass@martinsharehoodadmin.herokuapp.com/api/celery_proc_scalar",min_dynos=1,count_boundary=0,max_dynos=5"""

    engine = _get_database()
    Session = sessionmaker(bind=engine)
    session = Session()

    app = session.query(App).filter_by(appname=appname).first()

    if app is not None:
        print "App '%s' already exists, updating it" % appname
    else:
        print "Configuring new app for '%s'" % (appname)
        app = App(appname=appname)
        session.add(app)

    #app.control_app = control_app
    full_url = "https://%s.herokuapp.com/heroku_proc_scalar/proc_count" % appname

    if app_api_url:
        print "Got app_api url %s" % app_api_url
        url = urlparse(app_api_url)
        hostname = url.hostname
        scheme = url.scheme
        if scheme is None:
            scheme = 'https'
        port = url.port
        if port is not None:
            port = ":%s" % port
        else:
            port = ''
        path = url.path
        username = url.username
        password = url.password
        if password:
            app.password = password
        if username:
            app.username = username

        full_url = "%s://%s%s%s" % (scheme, hostname, port, path)

    app.app_api_url = full_url
    app.min_dynos = min_dynos
    app.max_dynos = max_dynos
    app.count_boundary = count_boundary

    HEROKU_API_KEY = os.environ.get('HEROKU_API_KEY', False)
    heroku_conn = heroku.from_key(HEROKU_API_KEY)
    heroku_app = heroku_conn.app(appname)
    print "Setting HEROKU_API_KEY directly from {0}".format(appname)
    config = heroku_app.config()
    new_api_key = config['HEROKU_API_KEY']
    app.api_key = new_api_key

    session.commit()
    print "Updated %s to :-" % appname
    print "appname = %s" % app.appname
    print "app_api_url = %s" % app.app_api_url
    print "username = %s" % app.username
    print "password = %s" % app.password
    print "min_dynos = %s" % app.min_dynos
    print "max_dynos = %s" % app.max_dynos
    print "count_boundary = %s" % app.count_boundary
    print "api_key = %s" % app.api_key


@task
def del_app(appname):
    engine = _get_database()
    Session = sessionmaker(bind=engine)
    session = Session()

    app = session.query(App).filter_by(appname=appname).first()

    if app is not None:
        session.delete(app)
        session.commit()
    else:
        print "No app called '%s' found" % appname


@task
def list_apps():
    engine = _get_database()
    Session = sessionmaker(bind=engine)
    session = Session()
    apps = session.query(App).order_by(App.appname).all()

    for app in apps:
        print "appname = %s" % app.appname
        print "app_api_url = %s" % app.app_api_url
        print "username = %s" % app.username
        print "password = %s" % app.password
        print "min_dynos = %s" % app.min_dynos
        print "max_dynos = %s" % app.max_dynos
        print "count_boundary = %s\n\n\n" % app.count_boundary
        print "api_key = %s\n\n\n" % app.api_key


@task
def initialise_project():

    engine = _get_database()
    App.metadata.create_all(engine)


@task
def update_api_keys_from_config():
    engine = _get_database()
    Session = sessionmaker(bind=engine)
    session = Session()
    apps = session.query(App).order_by(App.appname).all()

    HEROKU_API_KEY = os.environ.get('HEROKU_API_KEY', False)
    heroku_conn = heroku.from_key(HEROKU_API_KEY)
    heroku_apps = heroku_conn.apps()

    for app in apps:
        print "checking {0} for api_key".format(app.appname)
        if app.appname in heroku_apps:
            config = heroku_apps[app.appname].config()
            new_api_key = config['HEROKU_API_KEY']
            if new_api_key:
                print "[{0}] setting api_key to {1}".format(app.appname, new_api_key)
                app.api_key = new_api_key

    session.commit()


def _get_database():

    db_url = os.environ.get('DATABASE_URL', False)
    engine = create_engine(db_url)

    return engine

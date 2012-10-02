import os
from urlparse import urlparse
from fabric.api import task
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app import App


@task
def add_app(appname, app_api_url=False):

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

    full_url = "http://%s.herokuapp.com/api/proc_count" % appname

    if app_api_url is not None:
        url = urlparse(app_api_url)
        hostname = url.hostname
        scheme = url.scheme
        if scheme is None:
            scheme = 'http'
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

    session.commit()


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
def initialise_project():

    engine = _get_database()
    App.metadata.create_all(engine)


def _get_database():

    db_url = os.environ.get('DATABASE_URL', False)
    engine = create_engine(db_url)

    return engine

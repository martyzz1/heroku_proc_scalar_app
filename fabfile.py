import os
import sys
#import urllib2
from fabric.api import task, local, env, require, settings, hide
from fabric.utils import abort
#from unidecode import unidecode
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app import App


@task
def add_app(appname, domain=False, url_path=False):

    engine = _get_database()
    Session = sessionmaker(bind=engine)
    session = Session()

    app = session.query(App).filter_by(appname=appname).first()

    if app is not None:
        print "App '%s' already exists, updating it with domain = %s and url_path = %s" % (appname, domain, url_path)
        app.domain = domain
        app.url_path = url_path
    else:
        print "Configuring new app '%s' with domain = %s and url_path = %s" % (appname, domain, url_path)
        app = App(appname=appname, domain=domain, url_path=url_path)
        session.add(app)

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

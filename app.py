from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String

Base = declarative_base()


#http://docs.sqlalchemy.org/en/rel_0_7/orm/tutorial.html#create-an-instance-of-the-mapped-class
class App(Base):
    __tablename__ = 'app'
    appname = Column('appname', String(30), primary_key=True)
    app_api_url = Column('app_api_url', String(250))

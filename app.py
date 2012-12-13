from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Integer

Base = declarative_base()


#http://docs.sqlalchemy.org/en/rel_0_7/orm/tutorial.html#create-an-instance-of-the-mapped-class
class App(Base):
    __tablename__ = 'app'
    appname = Column('appname', String(30), primary_key=True)
    app_api_url = Column('app_api_url', String(250))
    username = Column('username', String(50), nullable=True)
    password = Column('password', String(50), nullable=True)
    min_dynos = Column('min_dynos', Integer(5), nullable=True)
    max_dynos = Column('max_dynos', Integer(5), nullable=True)
    count_boundary = Column('count_boundary', Integer(1), nullable=True)

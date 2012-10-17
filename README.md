heroku-proc-scalar
------------------

Heroku app for remotely Scaling heroku worker processes for multiple heroku apps based on api call to each app.
This app is designed to be run in conjunction with a server side api.
An Example app for controling CELERY workers (using REDIS backend) can be found here

    https://github.com/martyzz1/heroku_proc_scalar

In essence it expects a json response which contains a simple result list of "procname" to "count" like this:-

    {
        "celeryd": {
            "count": 2, 
            "active": 0
        }, 
        "celerybd": {
            "count": 99, 
            "active": 0
        }, 
        "celery_other": {
            "count": 0, 
            "active": 1
        },
        "someotherproc": {
            "count": 0, 
            "active": 0
        }
    }

The procname is the name of the process configured in your app's Procfile.
The count can be representative of anything you want. For me, I use this as a counter of the number of tasks in a Celery Queue. The idea being that when the count is 0 I scale the process to 0 to save me some money. 


Quick Setup
===========

    1. create a heroku app
    2. Clone this repository
    3. Configure your checkout to push to your heroku app
    4. issue a heroku deploy
        git push heroku master
    5. initialise the app (using the heroku CLI)
        heroku config:set DATABASE_URL=<your db_url> HEROKU_API_KEY=<your key> COUNT_BOUNDARY=1 SLEEP_PERIOD=10
        heroku run fab initialise_project
    6. Add your app to be monitored
        heroku run fab add_app:<yourappname>[,<your api_url>]   
    7. Scale up your worker
        heroku ps:scale worker=1


Configuration options
=====================

The following Environment Variables can be configured to tweak the behaviour of the worker process
configure this by setting your local envinronment variable, or on heroku using

    heroku config:set SLEEP_PERIOD=10 [--app <herokscalarapp>]
    heroku config:set COUNT_BOUNDARY=10 [--app <herokscalarapp>]

DATABASE_URL
============

This Specifies your postgres database url. You can get one by adding any of the postgres addons in heroku, then query your heroku config and copy the default configured URL to this variable e.g.

    1. heroku addons:add heroku-postgresql:dev
    2. heroku config [--app <herokuscalarapp>]
    == heroku-proc-scalar Config Vars
    HEROKU_POSTGRESQL_BLACK_URL: postgres://someuser:somepass@ec2-54-243-233-85.compute-1.amazonaws.com:5432/somepath
    3. heroku config:set DATABASE_URL=postgres://someuser:somepass@ec2-54-243-233-85.compute-1.amazonaws.com:5432/somepath
    
    resulting in:-
    4. heroku config [--app <herokuscalarapp>]
    = heroku-proc-scalar Config Vars
    DATABASE_URL:                postgres://someuser:somepass@ec2-54-243-233-85.compute-1.amazonaws.com:5432/somepath
    HEROKU_POSTGRESQL_BLACK_URL: postgres://someuser:somepass@ec2-54-243-233-85.compute-1.amazonaws.com:5432/somepath

HEROKU_API_KEY  = <KEY>
=====================================
Your Heroku api key found under your account at https://dashboard.heroku.com/account


SLEEP_PERIOD  = 10 (positive integer)
=====================================
The number of seconds the scalar will sleep before recommencing its polling of ALL configured apps


COUNT_BOUNDARY = 0  (any positive integers)
===========================================
The number of counts per Scaled process..
The default mode '0' simply says if count > 0 scale the proc to 1. if count is 0, scale the proc to 0.

e.g.  if the COUNT_BOUNDARY = 0(default)  and the returned json is as above, then we would scale as follows:-

    'celeryd' to 1 worker
    'celerybd' to 1 workers
    'celery_other' to 1 workers - until the active tasks finishes
    'someotherproc' to 0 workers

However if the COUNT_BOUNDARY is a positive integer, we use this to determine how many processes to scale to - loosly- using ROUND(INT(count/COUNT_BOUNDARY))
e.g.  if the COUNT_BOUNDARY = 10  and the returned json is as above, then we would scale as follows:-

    'celeryd' to 1 worker
    'celerybd' to 10 workers
    'celery_other' to 1 workers - until the active tasks finishes
    'someotherproc' to 0 workers


Adding an app to be scaled
--------------------------

The supplied fabric.py file contains the following functions

all functions can be called using heroku's run command
e.g. 

    heroku run <function>[:params] [--app <herokscalarapp>]

herokscalarapp is the name of the heroku app where you are deploying the scalar to run. You will only have to specify this is you have more than one configured in your .git/config

initialise_project
==================

Call this to create the projects database table


e.g. 
    
    heroku run fab initialise_project [--app herokscalarapp]


add_app
========
takes the following params
appname = name of the app you want to monitor and scale
app_api_url = optional url for specifying what url the scalar will query for its process information
    default = http://<appname>.herokuapp.com/api/scalar_tasks/

e.g  

    heroku run add_app:myherokuapp  [--app herokscalarapp]
    or
    heroku run add_app:myherokuapp,http://my.domain.com/api/path/to  [--app herokscalarapp]
    or
    heroku run add_app:myherokuapp,http://user:pass@my.domain.com/api/path/to  [--app herokscalarapp]

N.B. If you wish to specify a username and a password for accessing your app's api then you should specify it like

    heroku run add_app:myherokuapp,http://user:pass@<appname>.herokuapp.com/api/path/to  [--app herokscalarapp]
    

del_app
=======
Removes an app from being scaled and monitored


e.g. 
    heroku run del_app:<appname> [--app herokscalarapp]


list_Apps
=========
Lists all apps you are monitoring


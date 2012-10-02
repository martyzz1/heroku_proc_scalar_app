heroku-proc-scalar
====================

Scale heroku processes for multiple heroku apps based on api call to each app.

A sample api python view can be found in the examples directory.

In essence it expects a json response which contains a simple result list of "procname" to "count" like this:-

{
    'celeryd':2,
    'celerybd':99,
    'someotherproc':0
}

The procname is the name of the process configured in your app's Procfile.
The count can be representative of anything you want. For me, I use this as a counter of the number of tasks in a Celery Queue. The idea being that 
when the count is 0 I scale the process to 0 to save me some money. 

Configuration options
---------------------

The following Environment Variables can be configured to tweak the behaviour of the worker process
configure this by setting your local envinronment variable, or on heroku using
    heroku config:set SLEEP_PERIOD=10 [--app <herokscalarapp>]
    heroku config:set COUNT_BOUNDARY=10 [--app <herokscalarapp>]

SLEEP_PERIOD  = 10 (positive integer)
-------------------------------------
The number of seconds the scalar will sleep before commencing its polling of ALL configured apps


COUNT_BOUNDARY = 0  (any positive integers)
-------------------------------------------
The number of counts per Scaled process..
The default mode '0' simply says if count > 0 scale the proc to 1. if count is 0, scale the proc to 0
However if the COUNT_BOUNDARY is a positive integer, we use this to determine how many processes to scale to
e.g.  if the COUNT_BOUNDARY = 10  and the returned json is as above, then we would scale ias follows:-

    'celeryd' to 1 worker
    'celerybd' to 10 workers
    'someotherproc' to 0 workers


Adding an app to be scaled
===========================

The supplied fabric.py file contains the following functions

all functions can be called using heroku's run command
e.g. 
    heroku run <function>[:params] [--app <herokscalarapp>]

herokscalarapp is the name of the heroku app where you are deploying the scalar to run. You will only have to specify this is you have more than one configured in your .git/config

initialise_project
------------------

Call this to create the projects database table


e.g. heroku run fab initialise_project [--app herokscalarapp]


add_app
-------
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
-------
Removes an app from being scaled and monitored

e.g. 
    heroku run del_app:<appname> [--app herokscalarapp]


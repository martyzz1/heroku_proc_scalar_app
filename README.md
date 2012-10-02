heroku-proc-scalar
====================

Scale heroku processes for multiple heroku apps based on api call to each app
A sample api view can be found in the examples directory

Configuration options
====================

The following Environment Variables can be configured to tweak the beahviour of the worker process

SLEEP_PERIOD  = 10
The number of seconds the scalar will sleep before commencing its polling of ALL configured apps



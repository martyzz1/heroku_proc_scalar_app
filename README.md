heroku-proc-scalar
====================

Scale heroku processes for multiple heroku apps based on api call to each app
A sample api python view can be found in the examples directory

In essence it expects a json response which contains a simple result list of "procname" to "count" like this:-

{
    'celeryd':2,
    'celerybd':99,
    'someotherproc':0
}

The procname is the name of the process configured in your app's Procfile
The count can be representative of anything you want. For me, I use this as a counter of the number of tasks in a Celery Queue. The idea being that 
when the count is 0 I scale the process to 0 to save me some money. 

Configuration options
====================

The following Environment Variables can be configured to tweak the behaviour of the worker process

SLEEP_PERIOD  = 10 (positive integer)
The number of seconds the scalar will sleep before commencing its polling of ALL configured apps


COUNT_BOUNDARY = 0  (any positive integers)
The number of counts per Scaled process..
The default mode '0' simply says if count > 0 scale the proc to 1. if count is 0, scale the proc to 0
However if the COUNT_BOUNDARY is a positive integer, we use this to determine how many processes to scale to
e.g.  if the COUNT_BOUNDARY = 10  and the returned json is as above, then we would scale ias follows:-

    'celeryd' to 1 worker
    'celerybd' to 10 workers
    'someotherproc' to 0 workers


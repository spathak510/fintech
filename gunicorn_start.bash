#!/bin/bash
NAME="django_app"
DJANGODIR=/home/hello/proj_id_check/fintech_backend
SOCKFILE=/home/hello/proj_id_check/env/run/gunicorn.sock
USER=hello
GROUP=hello
NUM_WORKERS=3
DJANGO_SETTINGS_MODULE=hv_whatsapp.settings
DJANGO_WSGI_MODULE=hv_whatsapp.wsgi
TIMEOUT=120
LOGDIR=/home/hello/proj_id_check/env/logs  # Define log directory
ACCESS_LOG=$LOGDIR/gunicorn_access.log     # Access log file
ERROR_LOG=$LOGDIR/gunicorn_error.log       # Error log file


echo "Starting $NAME as 'whoami'"

# Activate the virtual environment

cd $DJANGODIR
source /home/hello/proj_id_check/env/bin/activate
export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE
export PYTHONPATH=$DJANGODIR:$PYTHONPATH

# Create the run and log directories if they don't exist
RUNDIR=$(dirname $SOCKFILE)
test -d $RUNDIR || mkdir -p $RUNDIR
test -d $LOGDIR || mkdir -p $LOGDIR

# Start your django unicorn

exec gunicorn ${DJANGO_WSGI_MODULE}:application \
	--name $NAME \
	--workers $NUM_WORKERS \
	--user=$USER --group=$GROUP \
	--bind=unix:$SOCKFILE \
	--log-level=debug \
	--timeout=$TIMEOUT \
	--access-logfile=$ACCESS_LOG \  # Log access information
    --error-logfile=$ERROR_LOG      # Log errors here

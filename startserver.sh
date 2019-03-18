#!/bin/bash
python localserver.py &
python -m utils.conv d
ls firebase -l
gunicorn --worker-class eventlet -w 1 server:app

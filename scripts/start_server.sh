#!/bin/bash
cd "/Users/emreuysal/Documents/Project/VivaCrm v2"
python manage.py runserver > server.log 2>&1 &
echo "Server started with PID $!"
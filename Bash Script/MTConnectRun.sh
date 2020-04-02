#!/bin/bash

/home/pi/cppagent/agent/agent &
python3 /home/pi/HaasMTConnect/HAAS_adapterv2.py &
python /home/pi/DatabaseFunctTest.py &

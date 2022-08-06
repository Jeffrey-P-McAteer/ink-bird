
# Inkbird pushover notification script

Requirements:

 - computer with bluetooth low energy
 - Python 3+
 - Pushover developer token (used for notifications)

Deployment:

 - Copy `inkbird.py` script (above) to computer
 - Set `PUSHOVER_USER_KEY` and `PUSHOVER_API_TOKEN` environment variables to your pushover credentials
 - Tweak any other settings at top of `inkbird.py`
 - Run the command `python inkbird.py`
 - Recieve notifications when temp is out of bounds



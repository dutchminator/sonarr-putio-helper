#!/bin/sh
# Bash script that sets up the proper user and kicks off the application

# Get PUID and GUID from environment, or set up default 1337 values
PUID=${PUID:-1337}
PGID=${PGID:-1338}

# Set up group and user with provided UID/GID
addgroup -g $PGID container-users && \
adduser -u $PUID -D -H -G container-users container-user

# Echo id output
echo "
Running as user/group: $(id container-user)
"

# Start the app as container-user
su -c "python /app/src/sonarr-putio-helper.py" container-user
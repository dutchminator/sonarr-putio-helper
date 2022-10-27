#!/bin/bash

# Bash script that sets up the proper user and kicks off the application

# Get PUID and GUID from environment, or set up default 1337 values
PUID=${PUID:-1337}
PGID=${PGID:-1337}

# Change the IDs for user container-user and group container-users
groupmod -o -g "$PGID" container-users
usermod -o -u "$PUID" container-user

# Echo output
echo "
User uid:    $(id -u container-user)
User gid:    $(id -g container-users)
"
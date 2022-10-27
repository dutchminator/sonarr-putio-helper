FROM python:3.10.7-alpine
LABEL Maintainer="Sebastiaan Candel <mail@sebastiaancandel.nl>"

# Install requirements
COPY requirements.txt /app/src/requirements.txt
RUN python -m pip install -r /app/src/requirements.txt

# Copy logic
COPY sonarr-putio-helper.py /app/src/sonarr-putio-helper.py
COPY init.sh /app/init.sh

# What user are we running as
RUN echo $(id)

# Start via init.sh
ENTRYPOINT sh app/init.sh
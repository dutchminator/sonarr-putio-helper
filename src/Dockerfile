FROM python:3.10.7-alpine
LABEL Maintainer="Sebastiaan Candel <mail@sebastiaancandel.nl>"

# Set up runtime user/group with placeholder IDs
RUN addgroup -g 13370 container-users && \
    adduser -u 13371 -D -H container-user container-users

# Install requirements
COPY requirements.txt /app/src/requirements.txt
RUN python -m pip install -r /app/src/requirements.txt

# Copy logic
COPY sonarr-putio-helper.py /app/src/sonarr-putio-helper.py

# Run the PUID/PGID init script
ENTRYPOINT ["bash", "init.sh"]

USER container-user

CMD ["python", "/app/src/sonarr-putio-helper.py"]

FROM python:3.12-alpine

ENV APP_HOME /usr/wren-api

WORKDIR ${APP_HOME}

# Install required system dependencies
# RUN apt update && apt install -y build-essential

# Copy entire file system
COPY ./ ./

# Install dependencies
RUN pip install -r requirements.txt

EXPOSE 7001

CMD [ "/bin/bash" ]
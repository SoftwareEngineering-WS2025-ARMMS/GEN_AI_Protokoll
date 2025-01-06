#!/bin/sh

if [ -e .venv/database_metadata.json ]
then
  echo "Using the metadata stored in the virtual environment directory"
  export $(jq -r 'to_entries | .[] | "\(.key)=\(.value)"' .venv/database_metadata.json)
  docker compose down --volumes
  docker compose up -d
  unset $(jq -r 'keys[]' .venv/database_metadata.json)
else
  # Used for test pipeline
  echo "Using the test metadata"
  export protocol_db_name="protocols_test"
  export protocol_server="protocol_server"
  export database_server_pwd="server_pwd"
  export host="localhost"
  export db_port=5800
  docker compose down --volumes
  docker-compose build --no-cache
  docker compose up --progres=plain
fi

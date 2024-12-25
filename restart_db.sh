#!/bin/sh

if [ -e .venv/database_metadata.json ]
then
  export $(jq -r 'to_entries | .[] | "\(.key)=\(.value)"' .venv/database_metadata.json)
  docker compose down --volumes
  docker compose up -d
  unset $(jq -r 'keys[]' db_config.json)
else
  # Used for test pipeline
  export protocol_db_name="protocols_test"
  export protocol_server="protocol_server"
  export database_server_pwd="server_pwd"
  export host="localhost"
  export db_port=5800
  docker compose down --volumes
  docker compose up -d
fi



#!/usr/bin/env bash
cd "$(dirname "$0")"

if ! command -v java &> /dev/null; then
  echo "Java not in path."
  exit 1
fi

if ! [ -f audio-dialogflow.jar ]; then
  echo "Required files not found, make sure you're in the right directory."
  exit 1
fi

cleanup() {
  echo -e "\nInterrupt received, stopping..."
  kill $dialogflow_pid
  exit 0
}

trap cleanup INT TERM

java -XX:+UseG1GC -jar audio-dialogflow.jar localhost &
dialogflow_pid=$!
echo "DialogFlow running (pid $dialogflow_pid)"
echo "Press Ctrl-C to stop."
wait

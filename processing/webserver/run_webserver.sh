#!/usr/bin/env bash
cd "$(dirname "$0")"

if ! command -v java &> /dev/null; then
  echo "Java not in path."
  exit 1
fi

if ! [ -f webserver.jar ]; then
  echo "Required files not found, make sure you're in the right directory."
  exit 1
fi

cleanup() {
  echo -e "\nInterrupt received, stopping..."
  kill $webserver_pid
  exit 0
}

trap cleanup INT TERM

java -jar webserver.jar localhost &
webserver_pid=$!
echo "Webserver running (pid $webserver_pid)"
echo "Press Ctrl-C to stop."
wait

#!/usr/bin/env bash
cd "$(dirname "$0")"

if ! command -v python &> /dev/null; then
  echo "Python not in path."
  exit 1
fi

if ! [ -f api_methods.py ]; then
  echo "Required files not found, make sure you're in the right directory."
  exit 1
fi

cleanup() {
  echo -e "\nInterrupt received, stopping..."
  kill $requests_pid
  exit 0
}

trap cleanup INT TERM

python api_methods.py &
requests_pid=$!
echo "Web Requests running (pid $requests_pid)"
echo "Press Ctrl-C to stop."
wait

#!/usr/bin/env bash
cd "$(dirname "$0")"

if ! command -v python &> /dev/null; then
  echo "Python not in path."
  exit 1
fi

if ! [ -f robot_memory.py ]; then
  echo "Required files not found, make sure you're in the right directory."
  exit 1
fi

cleanup() {
  echo -e "\nInterrupt received, stopping..."
  kill $memory_pid
  exit 0
}

trap cleanup INT TERM

python2 -u robot_memory.py &
memory_pid=$!
echo "Robot Memory running (pid $memory_pid)"
echo "Press Ctrl-C to stop."
wait

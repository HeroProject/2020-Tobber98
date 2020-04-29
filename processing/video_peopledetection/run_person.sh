#!/usr/bin/env bash
cd "$(dirname "$0")"

if ! command -v python2 &> /dev/null; then
  echo "Python2 not in path."
  exit 1
fi

if ! [ -f qi_person_detection.py ]; then
  echo "Required files not found, make sure you're in the right directory."
  exit 1
fi

cleanup() {
  echo -e "\nInterrupt received, stopping..."
  kill $person_pid
  exit 0
}

trap cleanup INT TERM

python2 qi_person_detection.py &
person_pid=$!
echo "Person Detection running (pid $person_pid)"
echo "Press Ctrl-C to stop."
wait

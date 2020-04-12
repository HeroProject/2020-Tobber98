#!/usr/bin/env bash
cd "$(dirname "$0")"

if ! command -v python &> /dev/null; then
  echo "Python not in path."
  exit 1
fi

if ! [ -f qi_face_recognition.py ]; then
  echo "Required files not found, make sure you're in the right directory."
  exit 1
fi

cleanup() {
  echo -e "\nInterrupt received, stopping..."
  kill $face_pid
  exit 0
}

trap cleanup INT TERM

python qi_face_recognition.py &
face_pid=$!
echo "Face Recognition running (pid $face_pid)"
echo "Press Ctrl-C to stop."
wait

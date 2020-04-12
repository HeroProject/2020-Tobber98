#!/usr/bin/env bash
cd "$(dirname "$0")"

if ! command -v python &> /dev/null; then
  echo "Python not in path."
  exit 1
fi

if ! [ -f emotion_detection.py ]; then
  echo "Required files not found, make sure you're in the right directory."
  exit 1
fi

cleanup() {
  echo -e "\nInterrupt received, stopping..."
  kill $emotion_pid
  exit 0
}

trap cleanup INT TERM

python emotion_detection.py &
emotion_pid=$!
echo "Emotion Detection running (pid $emotion_pid)"
echo "Press Ctrl-C to stop."
wait

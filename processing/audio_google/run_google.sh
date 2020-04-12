#!/usr/bin/env bash
cd "$(dirname "$0")"

if ! command -v python &> /dev/null; then
  echo "Python not in path."
  exit 1
fi

if ! [ -f google_speech_to_text.py ]; then
  echo "Required files not found, make sure you're in the right directory."
  exit 1
fi

cleanup() {
  echo -e "\nInterrupt received, stopping..."
  kill $google_pid
  exit 0
}

trap cleanup INT TERM

python google_speech_to_text.py &
google_pid=$!
echo "Google speech-to-text running (pid $google_pid)"
echo "Press Ctrl-C to stop."
wait

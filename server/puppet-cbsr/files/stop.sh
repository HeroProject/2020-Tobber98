#!/usr/bin/env bash
cd "$(dirname "$0")"

[ ! -f action_consumer.pid ] || pkill -F action_consumer.pid
[ ! -f event_producer.pid ] || pkill -F event_producer.pid
[ ! -f robot_sound_processing.pid ] || pkill -F robot_sound_processing.pid
[ ! -f visual_producer.pid ] || pkill -F visual_producer.pid
[ ! -f tablet_consumer.pid ] || pkill -F tablet_consumer.pid

rm -f *.pid *.log

#! /bin/bash

cd /home/epic/chirpp/chirpp/chirpp

while true
do
  if [[ $(ls ../.. | grep "Note_Detail") ]]
  then
    bash generate_report.sh
  else
    sleep 1h
  fi
done



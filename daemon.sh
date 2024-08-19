#! /bin/bash

cd ~

while true
do
  if [[ $(ls | grep "txt") ]]
  then
    chirpp/chirpp/generate_report.sh
  else
    sleep 1h
  fi
done

#! /bin/bash

set -oe pipefail

cd /home/epic/chirpp/chirpp

#source /home/epic/.bashrc
eval "$(conda shell.bash hook)"
conda activate chirpp_cpu

files=$(ls .. | grep "Note_Detail")

for file in $files
do
  echo $file
  python generate_report.py -c config.yaml -n ../$file -o ../reports/$file.xlsx 2> ../logs/$file.err
  if [ $? == 0 ]
  then
    # move files and encrypt them
    mv ../$file ../processed
    gpg -e -r epic_user ../processed/$file
    if [ $? == 0 ]
    then
      rm ../processed/file
    fi

    gpg -e -r epic_user ../reports/$file.xlsx
    if [ $? == 0 ]
    then
      rm ../reports/$file.xlsx
    fi
    echo "$file done"
  fi
done

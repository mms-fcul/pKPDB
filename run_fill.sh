#! /bin/bash

mkdir -p tmp
cd tmp
for i in {1..10}
do
    python3 ../src/fill.py
done

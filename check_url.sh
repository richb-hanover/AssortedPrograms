#!/bin/bash

base_url="http://doit2.box.com/s/"
# path="p564719X7iakX6mXXrs7XwXgvdy62tcXb"
path="p5647X97iakX6mXXrs7XwXgvdy62tcXb"
# https://doit2.app.box.com/s/p5647X97iakX6mXXrs7XwXgvdy62tcXb

# Generate all possible combinations by substituting "l" and "1" for "X"
combinations=("$path")

for (( i = 0; i < ${#path}; i++ )); do
    char="${path:$i:1}"
    if [[ "$char" == "X" ]]; then
        new_combinations=()
        for combo in "${combinations[@]}"; do
            new_combinations+=( "${combo:0:$i}l${combo:i+1}" )
            new_combinations+=( "${combo:0:$i}1${combo:i+1}" )
        done
        combinations=("${new_combinations[@]}")
    fi
done

# Test each generated combination and get the HTTP return status
for combo in "${combinations[@]}"; do
    url="${base_url}${combo}"
    http_status=$(curl -s -o /dev/null -w "%{http_code}" "$url")
    echo "URL: $url, HTTP Status: $http_status"
done

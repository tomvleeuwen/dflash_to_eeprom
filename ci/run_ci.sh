#!/usr/bin/env sh

cd $(dirname $0)

rm -r results
mkdir -p results/logs
mkdir -p results/eee

# Crude way to filter out any stacktraces from logfile:
# Just ignore all lines that start with at least two spaces
for file in $(ls input/dflash/) ; do
    echo "Converting ${file}"
    ../dflash_to_eee.py input/dflash/${file} results/eee/${file} 2>&1 | grep --text --invert-match "^  File" > results/logs/${file}
done

# Since we have set -e , a diff will automatically exit the script with an error.
set -e
for file in $(ls input/eee/) ; do
    echo "Checking results for ${file}"
    diff input/eee/${file} results/eee/${file}
done

# For now, just check if the logs match.
for file in $(ls input/logs/) ; do
    echo "Checking logs for ${file}"
    diff input/logs/${file} results/logs/${file}
done

echo "All results match"

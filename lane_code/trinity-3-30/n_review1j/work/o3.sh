X=/project/community/jjyeung/okh7/x_22c714e1; TZ=UTC date +%TZ >&2; cd $X/u < /dev/null
ls -la f41d15aadd7e0bde758a14806073424af2c3c70997efb8a0ce88226ace151ea5 c43379d754fb94a036795cb5c11432fcd4a6b1adfc02ee0992eeeba87aaba9e3 >&2
tar czf - f41d15aadd7e0bde758a14806073424af2c3c70997efb8a0ce88226ace151ea5 c43379d754fb94a036795cb5c11432fcd4a6b1adfc02ee0992eeeba87aaba9e3 --ignore-failed-read 2>/dev/null | head -c 15000000

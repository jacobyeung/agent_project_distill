export TZ=UTC; date -u +%TZ
squeue -j 174198 -h -o '%T|%M|%N|%L'
timeout 60 srun --overlap --jobid 174198 -N1 -n1 bash -c 'cd /tmp/a15_f16_174198/n && base64 -d | tar xzf - && sha256sum stop.sh wd.sh | cut -c1-16,65-' <<'B64'
H4sIABf+AWsAA+1Xe3PTRhDP3/oUiyIiCyzLsvMoNnKnA23oNIlnwExnSF1Gls72EelO6CQ7bpLv
3r2TFDsQl4EWmM7ol5lYj9Xu3r5XZDxpifnO10QbcXi4j7+H7kHb3fhVwMvOjnvQbbe7R0ftztEO
3nfd7g60v6pWJXKR+SnAzrt3K5Kz2Va6T73/n2L3gTOhzJn4Yq7twpReuoc9EBgUsPSjC1i64LMQ
yIKkq2xO2QxoBtJiGQmbkM0JgyTlC4KPW5ALf0aKrzGk4DwlvuBsjHxP/fSChJI0IEIQAV7BsnoC
fAoxZQSWcy4IELagKWcxYRkEfppS/OIn9+Dty9dn3tM0ZzDlUUjSATQEyYCzaAWUCRoSFIU6KdVN
AQJVn/BLqwW/pzRDHooyZ/gpOFmcOD7ynLqHb92jfffJDy1NcrNzjVwmPM1g9MZ7PXqmPffuoe2D
1MV47izdPpwMjz0D752Izxx1erzQhL9qWHAFJJhz0I1G6GcEucPjh7+MHo7eWGA80uEaMoJPfSRA
LnofbrSYeEaDhkhqabGym2IT8cCPIOnj2VNI8LzgSOM55237yfhRH0IO5+dgD5FTosN4DNfXEHCW
UZaTPmQpmH+0TfzHTOgMnJAsHJZHETyV9E5pcKnPLCUJ2O8vQa8sLo+mw95edZKrZLcQfaNLsYxI
rUdD1DopPs6RKCY62FMw/3RykaoQy2hMeI4GFjD6+eUp2BfQbYNS/zHI+LvPJw5zZlwGEwbi2SvD
RAXnxEfjuJZ2vE3klzBDb4Gu4r5hXLk9O/ZZ7kc3Vg8qvRP0yblxNRrejKFgUz45lk8KT+Fto7y6
LmyO5sY/awxpgNkVEUkR+BmqWwVMGuibHrHGuhaRaeZt4aTRqXI0QxaSTvq6X2TiBUWH2sq46tUm
2z6IiKClMHKn9EsFKCP99uvJCWS8PHGvEIWRUEhXb7dK7yrpu6X9CAsFTDB3M0GiKeY+isBrtGtC
IlkNJIESrWpKgqpWzgh8xngGWGEwFbImCC4LU4z6YXFagQ9/8XhCiSaThcpkcaEDXdiHg9tMkec7
HqrAtsMymfCBvMds9ZcXYF4lKcUSZHRvzDUBZrh/53CWDg88eFPm3AR1uqjO2ykSZNOk/7HIj11f
iLjH+B1l/G+kioqDraq4ZRxI11YuXfpi7WYML9lVNop5RGOa9W9LmupDHAlQG1oEglDBE8xpFBZN
6xLvN887+vC8o+GHaj8bno1Kyq3h+3kcS0Ns4VgYQuUVMuDTXlVIVAZtrSb9MoP8iC6w4xqNf3Ip
xmVVvFfYBDFG1TXjVv/W+B8xuv9k2xjpGlp/XYS5LI1eM1H/ZcB4TSIleU0/nQkPbHtJw2wOnXa7
6jhmWarN2xa0AJuUlwRM5pRjhVneLsPbG1DCTRgUXbSVCP2OSRMZPQw1Zn4sR5hSFEyInBkEeosW
oafCpoi5LJiHfCYtUqgQQGvN3Sr5z5JcSBLsniH1bRFTPNr7HAcbG195FCeNy2ZMYp6uWrlAN9o2
FqQY7RGIRZNx2X1wFtnsxxuO7psW+Akqf36vhIDHSZ4RW5J4aOmmlPC2kPbZgrDpfO9JtMb3gEqj
ryzjE/tf+xB3vrv7H85rR/X+9y1w7/6HPVVWwRn2BAa4A6k2gU05xKLXePGid3rae/XKat7dE5cU
K3pZpFvwMmdCzl2yJfMljo5ybbNtbOpphDObyEjyOfuWNvLWGxQ2Jb1QRo7qP97ouFMJbGZnFY28
1bbuXVVxV/O7YZTrLm6gctnFeceVR25K5Y1GY2SfWRYIHQYDUOve3SUPZ4FGA0bYes7AsqoxWbV2
Q72wyxfY5dVagjxuW9lakwGsC3NnsOfWxbhGjRo1atSoUaNGjRo1atSoUaNGjRo1avw7/A2U5qR8
ACgAAA==
B64
timeout 60 srun --overlap --jobid 174198 -N1 -n1 bash -s <<'EOS'
export TZ=UTC
TO=$(pgrep -u $(id -u) -f '^/usr/bin/timeout -s TERM -k 30 [0-9]+ bash /tmp/a15_f16_174198/n/go.sh w1 NS$' | head -1)
echo "timeout pid [$TO] state before: $(awk '{print $3}' /proc/$TO/stat 2>/dev/null)"
[ -n "$TO" ] && kill -STOP "$TO"; sleep 1
echo "timeout pid [$TO] state after STOP: $(awk '{print $3}' /proc/$TO/stat 2>/dev/null) (T = stopped; its 21:12:00Z timer can no longer act)"
echo "$(date -u +%FT%TZ) limit moved: timeout pid $TO stopped (state $(awk '{print $3}' /proc/$TO/stat)); the watchdog stops w1 at 21:45:00 UTC" >> /tmp/a15_f16_174198/w1/log/stop.log
EOS
nohup setsid srun --overlap --jobid 174198 -N1 -n1 bash /tmp/a15_f16_174198/n/wd.sh 21:45:00 > /dev/null 2>&1 < /dev/null &
echo "started watchdog srun pid $! at $(date -u +%TZ)"
sleep 5
timeout 60 srun --overlap --jobid 174198 -N1 -n1 bash -c 'cat /tmp/a15_f16_174198/w1/log/stop.log; ps -u $(id -u) -o pid=,stat=,etime=,args= --width 150 | grep "a15_f16" | grep -v grep | cut -c1-150'
pgrep -u $(id -u) -af 'srun --overlap --jobid 174198' | cut -c1-160
date -u +%TZ

cat > /tmp/c21sha <<"Y"
94aa116701211acd4f94d2accadbff5d41ba3589a415b8131d676e285aba0d57  a37de5787ed/result.tar.gz
89de2e04bfd7cf188d817b926c0dded70faedf287a172abfb85ffe2471223914  b01ec87a6f29b00029a7c/result.tar.gz
a2bc039a9b783c8d5b2ec494a784bdfc8e693bce6dd3b1fcf0024d3ec7ef9f71  b01ec87a6f29b00029a87/result.tar.gz
cb45b439637a37d55c40a9d77944506ef98e783f3a75951ae9cf7fe2ef50a1c1  b01ec87a6f29b00029ab2/result.tar.gz
4c8848bcc3a018764569bc4dbc84f2228dbc8208cad91afffc92b199e05842dc  b01ec87a6f29b00029ac6/result.tar.gz
48d1f2c71d920e796b789dfd8d4889ceeb46b99f0d274cd55f497e0cd5afa4be  b01ec87a6f29b00029ad2/result.tar.gz
d19f428e6d1ef668f8f35727836b50b5436236777e5077922b85c89a68ef9e17  bf94a7976a7e900029b5e/result.tar.gz
d4a0fb25fded39ab92e193a0dc5347879f4b10b48011b7dd7d4d476fed9d5e5c  e09e45fda45db00029c87/result.tar.gz
Y
set -u; cd /project/community/jjyeung/okh7/ae71c903
while read h f; do n=${f%%/*}; o=$(sha256sum $f | cut -d' ' -f1); if [ "$o" = "$h" ] && [ ! -e ../ae71c903_fetched/$n ]; then mv $n ../ae71c903_fetched/$n && echo "moved $n"; else echo "skip $n $o"; fi; done < /tmp/c21sha
du -sb /project/community/jjyeung/okh7/ae71c903

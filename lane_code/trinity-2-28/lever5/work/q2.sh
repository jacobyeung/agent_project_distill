ls -la /project/community/jjyeung/ac794e028b16f /project/community/jjyeung/ae63d9b7124fc 2>&1 | head -30; J=174200; TZ=UTC sacct -j $J -X -n -o State,Start,Elapsed,NodeList | tr -s " "

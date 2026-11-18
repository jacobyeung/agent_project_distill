export TZ=UTC; K=/project/community/jjyeung/okh7/x_3fdda0fb; sacct -j 170662 -X -n -o State,ExitCode,Start,End,Elapsed,NodeList%25; ls -la $K/o; head -c 3000 $K/o/170662.proof.json; echo; tail -n 30 $K/o/170662.proof.err | cut -c1-300; tail -n 10 $K/o/170662.proof.out | cut -c1-300
tail -n 40 /project/community/jjyeung/okh7/x_3fdda0fb/o/170662.proof.log | cut -c1-300

export TZ=UTC
sacct -j 170008 -X -o JobID,JobName%24,State,ExitCode,Start,End,Elapsed,NodeList -P
ls -la /project/community/jjyeung/okh7/x27ret/a8acc277397/ 2>&1 | head -30

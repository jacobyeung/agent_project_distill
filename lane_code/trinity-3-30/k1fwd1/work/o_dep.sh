scontrol update JobId=173346 Dependency=; echo rc=$?; sleep 20; TZ=UTC squeue -u $USER -o "%i %j %P %T %M %N %R"

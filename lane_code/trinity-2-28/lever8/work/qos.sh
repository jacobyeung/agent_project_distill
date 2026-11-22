TZ=UTC scontrol show job 174439 | grep -o -E '(QOS|Partition|Reason|Account|ExcNodeList|Requeue|JobState)=[^ ]*' | tr '\n' ' '; echo
TZ=UTC sacct -j 174328 -X -n -P -o JobID,Partition,QOS,Account
sacctmgr -n -P show assoc user=jjyeung format=account,partition,qos 2>/dev/null | head
scontrol show partition preempt | grep -o -E '(AllowQos|QoS|AllowAccounts|DenyQos)=[^ ]*' | tr '\n' ' '; echo

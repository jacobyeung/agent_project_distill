#!/bin/bash
# EFA probe inside the training image: devices, verbs provider, libfabric efa provider under two library orders.
set +e
echo "== container: $(. /etc/os-release; echo "$PRETTY_NAME") memlock $(ulimit -l) glibc $(ldd --version | head -1)"
ls -la /dev/infiniband | head -5; ls /sys/class/infiniband | head -4; cat /etc/libibverbs.d/efa.driver
ls /usr/lib/x86_64-linux-gnu/libibverbs | head; ls /opt/amazon/efa/lib | head -40; ls /opt/aws-ofi-nccl/lib
for order in "/opt/aws-ofi-nccl/lib:/opt/amazon/efa/lib:/opt/efa_hostlib" "/opt/amazon/efa/lib:/opt/efa_hostlib" "/opt/amazon/efa/lib"; do
    echo "=== LD_LIBRARY_PATH=$order"
    LD_LIBRARY_PATH="$order" ldd /opt/amazon/efa/bin/fi_info | grep -E "fabric|verbs|efa|not found"
    LD_LIBRARY_PATH="$order" FI_LOG_LEVEL=warn FI_EFA_USE_DEVICE_RDMA=1 timeout 60 /opt/amazon/efa/bin/fi_info -p efa -t FI_EP_RDM 2>&1 | head -14
    LD_LIBRARY_PATH="$order" ldd /opt/aws-ofi-nccl/lib/libnccl-net.so | grep -E "fabric|verbs|efa|cuda|not found"
done
echo "=== hmem"; LD_LIBRARY_PATH="/opt/amazon/efa/lib:/opt/efa_hostlib" FI_LOG_LEVEL=info FI_EFA_USE_DEVICE_RDMA=1 timeout 60 \
    /opt/amazon/efa/bin/fi_info -p efa -t FI_EP_RDM -c FI_HMEM 2>&1 | grep -iE "hmem|cuda|error|warn|provider" | head -20
ls /usr/lib/x86_64-linux-gnu | grep -E "^libcuda|^libnvidia-ml" | head

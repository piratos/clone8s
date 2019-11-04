docker run -d -p 4001:4001 -p 2380:2380 -p 2379:2379 \
 quay.io/coreos/etcd:v2.3.8 \
 -name etcd0 \
 -advertise-client-urls http://localhost:2379,http://localhost:4001 \
 -listen-client-urls http://0.0.0.0:2379,http://0.0.0.0:4001 \
 -initial-advertise-peer-urls http://localhost:2380 \
 -listen-peer-urls http://0.0.0.0:2380 \
 -initial-cluster-token etcd-cluster-1 \
 -initial-cluster etcd0=http://localhost:2380 \
 -initial-cluster-state new

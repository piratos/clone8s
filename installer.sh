#! /bin/bash

# Build images
echo "[+] Building needed images"
cd miniapiserver && docker build -t apiserver . -q && cd - >/dev/null
echo "[+] MiniApiServer image built successfully"
cd miniapiserver/dockerfiles && docker build -t minietcd . -q && cd - >/dev/null
echo "[+] MiniEtcd image built successfully"

# Prepare virtualenv for minikubelet
echo "[+] preparing virtualenv for minikubelet"
cd minikubelet
virtualenv -p python3 . >/dev/null
pip3 install -r requirements.txt >/dev/null

# Push etcd and apiserver manifests into minikubelet
echo "[+] Enabling etcd on minikubelet"
cp etcd.yaml manifests
echo "[+] Enabling apiserver on minikubelet"
cp apiserver.yaml manifests

# Finish
echo "[+] To start minikubelet, run:"
echo "source bin/activate
	python3 main.py"

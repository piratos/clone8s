# Clone8s
**is** a minimalistic kubernetes clone written in python for educational purposes only

A medium article will be published after this project is Ended

**isnt** a project meant to be maintained, a project that can be used in production or even for personal use, also it will be buggy :)

**Clone8s** is rather a thought experiement to try to understand the internal of kubernetes

Current status:
## mini Kubelet
A first iteration has been added with the following functionalities:
- Add pod (create)
- Update pod
- Delete pod
- Register to an etcd and verify against its root CA
- Read a given queue where apiserver or other process has been pushing events
- Read manifests from a local folder and handle addition/update/delete manifest files

## mini ApiServer
A first iteration has been added with the follwoing functionalities:
- serve api object on a threaded flask restful api
- etcd connection and logic to save objects into etcd cluster (only node and pod objects for now)
- rabbitMQ as a message broker, now all events should be pushed to a queue where some other process consume from it
The Pod spec is very simple
```
version: v0
name: dummy pod
namespace: podnamespace
hostNetwork: true
ip: 0.0.0.0 # forcing an ip for testing purposes
containers:
    - name: container1
      image: longrunningcontainer
    - name: container2
      image: longrunningcontainer
```
TODOs:
1. enrich the pod definition (and spec) with extra info for volumes
2. ~Create better ingest mechanism than the file based (file based and queue based podspec are in place)~
3. Gather system stats
4. ~Mock an api server and Create events to push to it~ (Api server in place and can be run as pod)
5. ~Design a registration handshake~ (Done)
6. ...

## Test so far
1. Create miniapiserver image
```
cd miniapiserver
docker build -t miniapiserver .
```
2. Create an etcd image
```
cd miniapiserver/dockerfiles
docker build -t minietcd
```
3. Start MiniKubelet
```
cd minikubelet
python3 main.py
```
4. create apiserver and etcd pods
```
#> cat apiserver.yaml
version: v0
name: apiserver
namespace: master
hostNetwork: true
#ip: 0.0.0.0 # forcing an ip for testing purposes
containers:
    - name: apiserver
      image: miniapiserver
    - name: rbmq-sidecar
      image: rabbitmq:3.8.1-management
 
 #> cat etcd.yaml
 version: v0
name: etcd
namespace: master
hostNetwork: true
#ip: 0.0.0.0 # forcing an ip for testing purposes
containers:
    - name: apiserver
      image: minietcd
 ```
 5. Put the etcd.yaml and the apiserver.yaml in the manifest folder as passed to minikubelet (check the call function in main.py)
 6. etcd and apiserver pods will start running and minikubelet will register to apiserver and start listening for events
## Rest of the components not implemented yet

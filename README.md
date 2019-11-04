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
- read a given queue where apiserver or other process has been pushing events

## mini ApiServer
A first iteratio has been added with the follwoing functionalities:
- serve api object on a threaded flask restful api
- etcd connection and logic to save objects into etcd cluster (only node objects for now)
- rabbitMQ as a message broker, now all events should be pushed to a queue where some other process consume from it
The Pod spec is very simple
```
version: v0
name: dummy pod
namespace: podnamespace
containers:
    - name: container1
      image: longrunningcontainer
    - name: container2
      image: longrunningcontainer
```
TODOs:
1. enrich the pod definition (and spec) with extra info for networking and volumes
2. ~Create better ingest mechanism than the file based (events should be pushed to minikublet queue somehow)~
3. Gather system stats
4. ~Mock an api server and Create events to push to it~
5. ~Design a registration handshake~
6. ...

## Rest of the components not implemented yet

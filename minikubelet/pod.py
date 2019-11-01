#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2019 piratos <piratos@zitoun>
#
# Distributed under terms of the MIT license.

"""
This module handle the object Pod
PodSpec
name: podname
namespace: podnamespace
containers:
    - name: container1name
      image: container1Image
    - name: container2name
      image: container2Image
"""

import yaml


class Container(object):
    def __init__(self, name, image, container=None):
        self.name = name
        self.image = image
        self.networked = False
        # docker-py container object
        self.container = container

class PodInterface(object):
    def __init__(self, podspec):
        """
        podspec: spec ofthe pod
        podspec: str
        """
        self.spec = yaml.safe_load(podspec)
        self.name = self.spec['name'].replace(' ', '_')
        self.containers = []
        self.parent_container = Container(
            name = "{}-pause".format(self.name),
            image = "kubernetes/pause:latest"
        )
        self.ip = None
        self.created = False
        self.containers_spec = self.spec['containers']
        # Create container objects
        for container in self.containers_spec:
            self.containers.append(
                Container(
                    name="{0}-{1}".format(
                        self.name,
                        container['name'].replace(' ', '_')
                        ),
                    image=container['image']
                )
            )
        # client
        self.client = None

    def create(self):
        if len(self.containers) < 1:
            print("Nothing to be done no containers")
            return True
        # Start by creating a pause container as parent
        pause_container = self.client.containers.create(
            name = self.parent_container.name,
            image = self.parent_container.image,
            detach = True
        )
        self.parent_container.container = pause_container
        # Create the docker-py containers
        parent_mode = "container:{0}".format(self.parent_container.name)
        for container in self.containers:
            # TODO: Add cgroup parent
            container.container = self.client.containers.create(
                name = container.name,
                image = container.image,
                detach = True,
                network = parent_mode,
                ipc_mode = parent_mode,
                pid_mode = parent_mode,
            )
        self.created = True

    def reload(self):
        # reload all containers
        for container in self.containers:
            container.container.reload()

    def start(self):
        # Create the Pod containers for the first time
        if not self.created:
            self.create()
        # start parent container first
        self.parent_container.container.start()
        # start the pod containers (order does not matter)
        for container in self.containers:
            container.container.start()

    def stop(self):
        # stop non pause containers first
        for container in self.containers:
            # Only kill running container
            container.container.reload()
            if container.container.status == "running":
                container.container.kill()
        self.parent_container.container.kill()
        # TODO: look for prune per kill
        self.client.containers.prune()

    def status(self, info=False):
        # reload and return status
        running = 0
        failed = []
        for container in self.containers:
            container.container.reload()
            if container.container.status == "running":
                running += 1
            else:
                failed.append(container)
        short_res =  "{0}/{1}".format(running, len(self.containers))
        long_res = "\n".joint([
                "container {0} failed".format(c) for c in failed])
        if info:
            return "{0}\n{1}".format(short_res, long_res)
        return short_res

    def logs(self, container_name=None):
        # return the logs of given container or all containers
        if container_name and \
            container_name in [c.name for c in self.containers]:
            return {container.name: container.container.logs()}
        else:
            logs = {}
            for container in self.containers:
                logs[container.name] = container.container.logs()
            return logs
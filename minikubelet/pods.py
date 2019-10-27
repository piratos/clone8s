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
        self.spec = yaml.load(podspec)
        self.name = self.spec['name'].replace(' ', '_')
        self.containers = []
        self.netcontainer = None
        self.ip = None
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

    def start(self):
        # To make containers share the same network interface
        # we need the first to connect to a network
        # and the rest to use network mode 'container'
        if len(self.containers) < 1:
            print("Nothing to be done no containers")
            return True
        self.netcontainer = self.containers.pop(0)
        self.netcontainer.networked = True
        # Create the docker-py containers
        # TODO: Use Create + start instead of run
        self.netcontainer.container = self.client.containers.run(
            name = self.netcontainer.name,
            image = self.netcontainer.image,
            detach = True
        )
        for container in self.containers:
            container.container = self.client.containers.run(
                name = container.name,
                image = container.image,
                detach = True,
                network = "container:{0}".format(self.netcontainer.name)

            )

    def stop(self):
        # stop non networked container first
        for container in self.containers:
            container.container.kill()
        self.netcontainer.container.kill()
        # TODO: look for prune per kill
        self.client.containers.prune()

    def status(self):
        # reload and return status
        statuses = []
        self.netcontainer.container.reload()
        statuses.append(self.netcontainer.container.status)
        for container in self.containers:
            container.container.reload()
            statuses.append(container.container.status)
        return statuses


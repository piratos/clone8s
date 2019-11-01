from base import BaseManager


class LogManager(BaseManager):
	def logs(self, pod_name, container_name=None):
		if pod_name in self.k.pods:
			return self.k.pods[pod_name].logs(
				container_name=container_name)
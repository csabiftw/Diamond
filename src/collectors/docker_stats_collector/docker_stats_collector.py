# coding=utf-8

"""
The DockerStatsCollector uses the docker stats api to collect data about docker and the containers.

#### Dependencies

* docker -- Install via `pip install docker-py`.
  Source https://github.com/docker/docker-py
"""

import json
import diamond.collector

try:
	import docker
except ImportError:
	docker = None
	 
class DockerStatsCollector(diamond.collector.Collector):

	# path in stats json : metric tag
	METRICS = {
			# memory stats
			"memory_stats.stats.rss" : "memory.rrs",
			"memory_stats.stats.total_rss" : "memory.total_rrs",
			"memory_stats.stats.total_cache" : "memory.total_cache",
			"memory_stats.stats.total_swap" : "memory.total_swap",
			"memory_stats.stats.total_pgpgin" : "memory.total_pgpgin",
			"memory_stats.stats.total_pgpgout" : "memory.total_pgpgout",

			# cpu stats
			"cpu_stats.cpu_usage.total_usage" : "cpu.total",
			"cpu_stats.cpu_usage.usage_in_kernelmode" : "cpu.kernelmode",
			"cpu_stats.cpu_usage.usage_in_usermode" : "cpu.usermode",
			"cpu_stats.system_cpu_usage" : "cpu.system",

			# network stats
			"networks.eth0.rx_bytes" : "network.rx_bytes",
			"networks.eth0.rx_packets" : "network.rx_packets",
			"networks.eth0.rx_errors" : "network.rx_errors",
			"networks.eth0.rx_dropped" : "network.rx_dropped",
			"networks.eth0.tx_bytes" : "network.tx_bytes",
			"networks.eth0.tx_packets" : "network.tx_packets",
			"networks.eth0.tx_errors" : "network.tx_errors",
			"networks.eth0.tx_drop" : "network.tx_drop",
	}

	def get_default_config_help(self):
		config_help = super(DockerStatsCollector, self).get_default_config_help()
		return config_help

	def get_default_config(self):
		config = super(DockerStatsCollector, self).get_default_config()
		config.update({
			'path': 'docker_stats'
		})
		return config

	def get_value(self, path, dictionary):
		keys = path.split(".")
		cur = dictionary
		for key in keys:
			if not isinstance(cur, dict):
				raise Exception("metric path '{0}'' does not exist in docker stats output".format(path))
			cur = cur.get(key)
			if cur == None:
				break
		return cur

	def collect(self):
		if docker is None:
			self.log.error('Unable to import docker')

		try:
			# Collect info
			results = {}
			client = docker.Client(version='auto')

			# Top level stats
			running_containers = client.containers()
			results['containers_running_count'] = (
				len(running_containers), 'GAUGE')

			all_containers = client.containers(all=True)
			results['containers_stopped_count'] = (
				len(all_containers) - len(running_containers), 'GAUGE')

			images_count = len(set(client.images(quiet=True)))
			results['images_count'] = (images_count, 'GAUGE')

			dangling_images_count = len(set(client.images(
				quiet=True, all=True, filters={'dangling': True})))
			results['images_dangling_count'] = (dangling_images_count, 'GAUGE')

			# Collect memory and cpu stats
			for container in running_containers:
				env_var_name = "JOB_NAME"
				real_name = "UNKNOWN_NAME"
				
				env_vars = client.inspect_container(container["Id"])["Config"]["Env"]
				try: 
					real_name = [e.split("=")[1] for e in env_vars if e.startswith(env_var_name)][0]
				except IndexError, e:
					pass
				name = container['Names'][0][1:]
				s = client.stats(container["Id"])
				stat = json.loads(s.next())
				for path in self.METRICS: 
					val = self.get_value(path, stat)
					if val is not None:
						results[".".join([real_name, name, self.METRICS.get(path)])] = (val, 'GAUGE')
				s.close()

			for name in sorted(results.keys()):
				(value, metric_type) = results[name]
				self.publish(name, value, metric_type=metric_type)

		except Exception, e:
			self.log.error(e, exc_info=True)
from multimodule import FastModulAut as multi
import start_topology as top

def create_service(data):
	def peagg(data):
		pass
	def bpe(data):
		pass
	def rgr(data):
		pass


if __name__ == "__main__":
	# devices = ['10.200.72.176', '10.200.72.177']
	devices = ['10.200.72.176']
	data = {'ok': True, 'error': '', 'class': 'L2', 'router': {'name': '', 'ip': '', 'model': ''}, 'switch': {'name': '', 'ip': '', 'model': ''}}
	create_service(data)
	for device in devices:
		result = top.loop(device)
		print(f"\nCREATE VPN\n{result}")


restart-monitor:
	sudo docker-compose -f docker-compose.monitor.yml down
	sudo docker-compose -f docker-compose.monitor.yml up -d

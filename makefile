restart-monitor:
	sudo docker-compose -f docker-compose.monitor.yml down
	sudo docker-compose -f docker-compose.monitor.yml up -d --build


restart-server:
	sudo docker-compose down
	sudo docker-compose up -d --build

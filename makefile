start:
	poetry run python -m app.data.yahoo.realtime_stock.realtime_stock_app &
	poetry run python -m app.data.yahoo.exchange_rate.exchange_rate_app &
	poetry run python -m app.data.naver.realtime_index.realtime_index_app &
	poetry run celery -A app.data.celery_app.base.celery_task worker --beat --loglevel=info &


restart-monitor:
	sudo docker-compose -f docker-compose.monitor.yml down
	sudo docker-compose -f docker-compose.monitor.yml up -d


restart-realtime:
	sudo pkill -f realtime_stock_app.py || true
	sudo pkill -f realtime_stock_collector_world.py || true
	sudo pkill -f realtime_stock_collector_korea.py || true
	sudo pkill -f exchange_rate_app.py || true
	sudo pkill -f realtime_index_app.py || true

	poetry run python -m app.data.yahoo.realtime_stock.realtime_stock_app &
	poetry run python -m app.data.yahoo.exchange_rate.exchange_rate_app &
	poetry run python -m app.data.naver.realtime_index.realtime_index_app &
	poetry run python -m app.data.celery_app.base &

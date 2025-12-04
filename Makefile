img:
	docker build -t ghcr.io/aleksey925/alert-manager:${ver} . \
		&& docker tag ghcr.io/aleksey925/alert-manager:${ver} ghcr.io/aleksey925/alert-manager:latest

lint:
	pre-commit run --all

test:
	pytest --cov=alert_manager --cov-fail-under=72 ./tests

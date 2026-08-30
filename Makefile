UV ?= uv

.PHONY: install test train predict docker-build terraform-fmt

install:
	$(UV) sync

test:
	$(UV) run pytest -q

train:
	$(UV) run python -m src.train --epochs $${EPOCHS:-5}

predict:
	$(UV) run python -m src.predict $${IMAGE} --model $${MODEL:-artifacts/model.pt}

docker-build:
	docker build -t medops-lite:local .

terraform-fmt:
	terraform -chdir=terraform fmt -check

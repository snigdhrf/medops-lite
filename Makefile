UV ?= uv

.PHONY: install test train predict docker-build terraform-fmt

install:
	$(UV) sync

test:
	$(UV) run pytest -q

train:
	$(UV) run medops-train --epochs $${EPOCHS:-5}

predict:
	$(UV) run medops-predict $${IMAGE} --model $${MODEL:-artifacts/model.pt}

docker-build:
	docker build -t medops-lite:local .

terraform-fmt:
	terraform -chdir=terraform fmt -check

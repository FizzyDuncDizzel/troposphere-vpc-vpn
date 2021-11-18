# Invoke Runway

SHELL=bash

plan:
	python -m pipenv run runway plan

deploy:
	DEPLOY_ENVIRONMENT=common pipenv run runway deploy

deploy-dev:
	DEPLOY_ENVIRONMENT=dev pipenv run runway deploy

deploy-core:
	DEPLOY_ENVIRONMENT=common python -m pipenv run runway deploy --tag core

destroy:
	DEPLOY_ENVIRONMENT=common pipenv run runway destroy
destroy-dev:
	DEPLOY_ENVIRONMENT=dev pipenv run runway destroy

destroy-vpc:
	@pushd core.cfn && \
	@runway.cfngin destroy --force -t *.env core.yaml

verify:
	@echo "Test Successful!"

.PHONY: build serve server-container pause address stop-server restart-server lint \
	      test pytest isort black flake8 mypy shell

# Usage:
# make build            # build the docker image
# make serve            # serve the website
# make server-container # build server container
# make pause            # pause 1 second (to pause between commands)
# make address          # get Docker container address/port
# make stop-server      # stop the running web server
# make restart-server   # restart the running web server
# make lint             # run linters
# make test             # run full testing suite
# make pytest           # run pytest in docker container
# make isort            # run isort in docker container
# make black            # run black in docker container
# make flake8           # run flake8 in docker container
# make mypy             # run mypy in docker container
# make shell            # create interactive shell in docker container

################################################################################
# GLOBALS                                                                      #
################################################################################

# path related variables
CURRENTDIR := $(PWD)

# docker-related variables
DCTNR := webserver.$(notdir $(PWD))
SRCPATH = /usr/local/src/parley
DCKRIMG = ghcr.io/diogenesanalytics/parley:master
DCKRBLD = docker build -t ${DCKRIMG} . --load
DCKRUSR = --user 1000:1000
DCKRTST = docker run --rm ${DCKRUSR} -v ${CURRENTDIR}:${SRCPATH} -it ${DCKRIMG}

################################################################################
# COMMANDS                                                                     #
################################################################################

# build docker image
build:
	${DCKRBLD}

# serve the website
serve: server-container pause address

# build server container
server-container:
	@ echo "Launching web server in Docker container -> ${DCTNR} ..."
	@ if ! docker ps --format="{{.Names}}" | grep -q "${DCTNR}"; then \
		docker run -d \
		           --rm \
		           --name ${DCTNR} \
		           -p 8000 \
		           -v "${CURRENTDIR}":/usr/local/src/parley \
		           ${DCKROPT} \
		           ${DCKRIMG} \
		           python3 -m http.server 8000 && \
	  if ! grep -sq "${DCTNR}" "${CURRENTDIR}/.running_containers"; then \
	    echo "${DCTNR}" >> .running_containers; \
	  fi; \
	else \
	  echo "Container already running. Try setting DCTNR manually."; \
	fi

# simply wait for a certain amount of time
pause:
	@ echo "Sleeping 1 seconds ..."
	@ sleep 1

# get containerized server address
address:
	@ if [ -f "${CURRENTDIR}/.running_containers" ]; then \
	while read container; do \
	  if echo "$${container}" | grep -q "${DCTNR}" ; then \
	    echo "Server address: http://$$(docker port ${DCTNR}| grep 0.0.0.0: | \
			      awk '{print $$3}')"; \
	  else \
	    echo "Could not find running container: ${DCTNR}." \
	         "Try running: make list-containers"; \
	  fi \
	done < "${CURRENTDIR}/.running_containers"; \
	else \
	  echo ".running_containers file not found. Is a Docker container running?"; \
	fi

# stop all containers
stop-server:
	@ if [ -f "${CURRENTDIR}/.running_containers" ]; then \
	  echo "Stopping Docker containers ..."; \
	  while read container; do \
	    echo "Container $$(docker stop $$container) stopped."; \
	  done < "${CURRENTDIR}/.running_containers"; \
	  rm -f "${CURRENTDIR}/.running_containers"; \
	else \
	  echo "${CURRENTDIR}/.running_containers file not found."; \
	fi

# restart server
restart-server: stop-server serve

# run linters
lint: isort black flake8 mypy

# run full testing suite
test: pytest lint

# run pytest in docker container
pytest:
	@ ${DCKRTST} pytest

# run isort in docker container
isort:
	@ ${DCKRTST} isort tests/

# run black in docker container
black:
	@ ${DCKRTST} black tests/

# run flake8 in docker container
flake8:
	@ ${DCKRTST} flake8 --config=tests/.flake8

# run mypy in docker container
mypy:
	@ ${DCKRTST} mypy --ignore-missing-imports tests/

# create interactive shell in docker container
shell:
	@ ${DCKRTST} bash || true

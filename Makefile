SHELL:=/bin/bash
PRJDIR:=$(CURDIR)
DOCKER_COMPOSE:=CURRENT_USER=$$(id -u) docker-compose

build: docker-buildenv/.buildenv.built
	$(DOCKER_COMPOSE) -f docker-buildenv/docker-compose.yml run --rm buildenv make -C /debian-build/build build-in-buildenv

docker-buildenv/.buildenv.built: docker-buildenv/Dockerfile docker-buildenv/docker-compose.yml
	cp debian/control docker-buildenv/debian_control
	$(DOCKER_COMPOSE) -f docker-buildenv/docker-compose.yml build buildenv
	touch docker-buildenv/.buildenv.built

build-in-buildenv:
	USER="build" HOME="$(PRJDIR)" dpkg-buildpackage
	mkdir -p deb
	for i in $$(cat debian/files | awk '{print $$1}'); do cp ../$$i deb/; done
	cp ../*.changes deb/
	@echo -e "\nDebian-Build finished SUCCESSFULLY! Find Build-Results in folder ./deb/\n"

tests:
	make -C test

%.html: %.md
	sed "s/\.md)/\.html)/g" $< | pandoc -s --css styles.css -f markdown -t html -o $@ 

docs: README.html docs/Configuration.html

autoupdate_docs:
	while true; do sleep 2; make -s docs; done

manpages:
	tools/build_manpages.py

clean:
	rm -Rf docker-buildenv/.buildenv.built docker-buildenv/debian_control deb/ .cache/ \
	       README.html docs/*.html

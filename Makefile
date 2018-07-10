run_test:
	make -C test test

run_clitests:
	make -C test clitests

%.html: %.md
	sed "s/\.md)/\.html)/g" $< | pandoc -f markdown -t html >$@

docs: README.html docs/Configuration.html

manpages:
	tools/build_manpages.py

clean:
	rm -f README.html docs/*.html

run_test:
	make -C test test

run_clitests:
	make -C test clitests

README.html: README.md
	pandoc -f markdown -t html README.md >README.html

manpages:
	tools/build_manpages.py

clean:
	rm README.html

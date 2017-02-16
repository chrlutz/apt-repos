run_test:
	make -C test test

run_clitests:
	make -C test clitests

README.html: README.md
	pandoc -f markdown -t html README.md >README.html

clean:
	rm README.html

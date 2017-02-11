README.html: README.md
	pandoc -f markdown -t html README.md >README.html

clean:
	rm README.html

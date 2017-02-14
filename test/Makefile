TESTCASES = testPrintHelloWorld testSuiteSelectors testGetPackageFields testQueryResult

test:
	for i in $(TESTCASES); do \
                echo ""; \
                echo "----------------------------------------------------------"; \
		echo "Testing $$i"; \
                echo "----------------------------------------------------------"; \
		./test_lib_apt_repos.py $${i} > $${i}.res || exit 1; \
		diff -u $${i}.ref $${i}.res || exit 1; \
		echo "OK"; \
	done

clean:
	rm -Rf *.res .apt-repos_cache

EXP_OK := || exit 1
EXP_FAIL := && exit 1 || true
CLI := ../src/apt-repos -b $(realpath .)

UNIT_TESTCASES = testPrintHelloWorld \
            testSuiteSelectors \
            testGetPackageFields \
            testQueryResult \
            testQueryPackages \
            testGetSourcesFiles

test: unittests clitests

clitests: _cliTestHelpSystem _cliTestSuites _cliTestLs _cliTestShow

unittests: clean 
	for i in $(UNIT_TESTCASES); do \
                echo ""; \
                echo "----------------------------------------------------------"; \
		echo "Testing $$i"; \
                echo "----------------------------------------------------------"; \
		./test_lib_apt_repos.py $${i} \
                        | grep -v "Reading package lists..." \
                        | grep -v "Building dependency tree..." \
                        > $${i}.res || exit 1; \
		diff -u $${i}.ref $${i}.res $(EXP_OK); \
		echo "OK"; \
	done

clean:
	rm -Rf *.res .apt-repos_cache


_cliTestHelpSystem:
	echo "----------------------------------------------------------"
	$(CLI) >cliHelpTest1.res 2>&1 $(EXP_OK)
	diff -u cliHelpTest1.ref cliHelpTest1.res $(EXP_OK)
	
	$(CLI) -h >cliHelpTest2.res 2>&1 $(EXP_OK)
	diff -u cliHelpTest2.ref cliHelpTest2.res $(EXP_OK)
	
	$(CLI) -h unknown_command >cliHelpTest3.res 2>&1 $(EXP_FAIL)
	diff -u cliHelpTest3.ref cliHelpTest3.res $(EXP_OK)
	
	$(CLI) -h suites >cliHelpTest4.res 2>&1 $(EXP_OK)
	diff -u cliHelpTest4.ref cliHelpTest4.res $(EXP_OK)
	
	$(CLI) -h ls >cliHelpTest5.res 2>&1 $(EXP_OK)
	diff -u cliHelpTest5.ref cliHelpTest5.res $(EXP_OK)
	
	$(CLI) -h show >cliHelpTest6.res 2>&1 $(EXP_OK)
	diff -u cliHelpTest6.ref cliHelpTest6.res $(EXP_OK)
	echo "OK"

_cliTestSuites:
	echo "----------------------------------------------------------"
	$(CLI) suites >cliTestSuites1.res 2>&1 $(EXP_OK)
	diff -u cliTestSuites1.ref cliTestSuites1.res $(EXP_OK)
	echo "OK"

_cliTestLs:
	echo "----------------------------------------------------------"
	$(CLI) ls reprepro >cliTestLs1.res 2>&1 $(EXP_OK)
	diff -u cliTestLs1.ref cliTestLs1.res $(EXP_OK)
	
	$(CLI) ls reprepro -di a -dt diff_-y >cliTestLs2.res 2>&1 $(EXP_OK)
	diff -u cliTestLs2.ref cliTestLs2.res $(EXP_OK)
	echo "OK"

_cliTestShow:
	echo "----------------------------------------------------------"
	$(CLI) show reprepro >cliTestShow1.res 2>&1 $(EXP_OK)
	diff -u cliTestShow1.ref cliTestShow1.res $(EXP_OK)
	
	$(CLI) show reprepro -di s -s trusty,xenial -dt diff_-y >cliTestShow2.res 2>&1 $(EXP_OK)
	diff -u cliTestShow2.ref cliTestShow2.res $(EXP_OK)
	
	$(CLI) show reprepro -di s -s trusty,xenial -dt diff_-y_--suppress-common-lines >cliTestShow3.res 2>&1 $(EXP_OK)
	diff -u cliTestShow3.ref cliTestShow3.res $(EXP_OK)
	echo "OK"


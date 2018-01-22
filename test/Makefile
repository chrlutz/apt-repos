EXP_OK := || exit 1
EXP_FAIL := && exit 1 || true
CLI := ../src/apt-repos -b $(realpath .)
FINISHED_TEST = @echo "SUCCESSFULLY FINISHED TEST $@"; echo ""; echo "========================================================="
STARTING_TEST = @echo "STARTING TEST $@"

UNIT_TESTCASES = testPrintHelloWorld \
            testSuiteSelectors \
            testSuiteProperties \
            testGetPackageFields \
            testQueryResult \
            testQueryPackages \
            testGetSourcesFiles

test: unittests clitests

clitests: _cliTestHelpSystem _cliTestSuites _cliTestLs _cliTestShow _cliTestDsc

unittests: clean 
	$(STARTING_TEST)
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
	$(FINISHED_TEST)

clean:
	rm -Rf *.res .apt-repos_cache


_cliTestHelpSystem:
	$(STARTING_TEST)
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
	$(FINISHED_TEST)

_cliTestSuites:
	$(STARTING_TEST)
	$(CLI) suites >cliTestSuites1.res 2>&1 $(EXP_OK)
	diff -u cliTestSuites1.ref cliTestSuites1.res $(EXP_OK)
	
	$(CLI) suites --verbose >cliTestSuites2.res 2>&1 $(EXP_OK)
	diff -u cliTestSuites2.ref cliTestSuites2.res $(EXP_OK)
	
	$(CLI) suites --verbose -s trusty >cliTestSuites3.res 2>&1 $(EXP_OK)
	diff -u cliTestSuites3.ref cliTestSuites3.res $(EXP_OK)
	$(FINISHED_TEST)

_cliTestLs:
	$(STARTING_TEST)
	$(CLI) ls reprepro >cliTestLs1.res 2>&1 $(EXP_OK)
	diff -u cliTestLs1.ref cliTestLs1.res $(EXP_OK)
	
	$(CLI) ls reprepro -di a -dt diff,-y >cliTestLs2.res 2>&1 $(EXP_OK)
	diff -u cliTestLs2.ref cliTestLs2.res $(EXP_OK)
	
	$(CLI) ls zim -di a -dt diff,-y >cliTestLs3.res 2>&1 $(EXP_FAIL)
	diff -u cliTestLs3.ref cliTestLs3.res $(EXP_OK)
	
	$(CLI) ls zim git -di a -dt diff,-y >cliTestLs4.res 2>&1 $(EXP_FAIL)
	diff -u cliTestLs4.ref cliTestLs4.res $(EXP_OK)
	
	$(CLI) ls zim git -di a^all -dt diff,-y >cliTestLs5.res 2>&1 $(EXP_OK)
	diff -u cliTestLs5.ref cliTestLs5.res $(EXP_OK)
	$(FINISHED_TEST)

_cliTestShow:
	$(STARTING_TEST)
	$(CLI) show reprepro >cliTestShow1.res 2>&1 $(EXP_OK)
	diff -u cliTestShow1.ref cliTestShow1.res $(EXP_OK)
	
	$(CLI) show reprepro -di s -s trusty,xenial -dt diff,-y >cliTestShow2.res 2>&1 $(EXP_OK)
	diff -u cliTestShow2.ref cliTestShow2.res $(EXP_OK)
	
	$(CLI) show reprepro -di s -s trusty,xenial -dt diff,-y,--suppress-common-lines >cliTestShow3.res 2>&1 $(EXP_OK)
	diff -u cliTestShow3.ref cliTestShow3.res $(EXP_OK)
	$(FINISHED_TEST)

_cliTestDsc:
	$(STARTING_TEST)
	$(CLI) dsc reprepro >cliTestDsc1.res 2>&1 $(EXP_OK)
	diff -u cliTestDsc1.ref cliTestDsc1.res $(EXP_OK)
	
	$(CLI) dsc -s ubuntu: reprepro >cliTestDsc2.res 2>&1 $(EXP_OK)
	diff -u cliTestDsc2.ref cliTestDsc2.res $(EXP_OK)
	
	$(CLI) dsc -s ubuntu: notexistent >cliTestDsc3.res 2>&1 $(EXP_FAIL)
	diff -u cliTestDsc3.ref cliTestDsc3.res $(EXP_OK)
	
	$(CLI) dsc -c main -s ubuntu: reprepro >cliTestDsc4.res 2>&1 $(EXP_FAIL)
	diff -u cliTestDsc4.ref cliTestDsc4.res $(EXP_OK)
	
	$(CLI) dsc -c universe -s ubuntu: reprepro >cliTestDsc5.res 2>&1 $(EXP_OK)
	diff -u cliTestDsc5.ref cliTestDsc5.res $(EXP_OK)	

	$(CLI) dsc reprepro zim git >cliTestDsc6.res 2>&1 $(EXP_OK)
	diff -u cliTestDsc6.ref cliTestDsc6.res $(EXP_OK)	

	$(CLI) dsc -1 reprepro zim git >cliTestDsc7.res 2>&1 $(EXP_OK)
	diff -u cliTestDsc7.ref cliTestDsc7.res $(EXP_OK)	
	$(FINISHED_TEST)


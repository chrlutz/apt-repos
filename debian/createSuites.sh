#!/bin/bash
###############################################################
# creates suite files
###############################################################


suiteEntry()
{
    local suite=$1
    cat <<__ENDL
    {
      "Suite" : "${REPO}:${suite}",
      "SourcesList" : "deb ${URL} ${suite} ${COMPONENTS}",
      "DebSrc" : true,
      "Architectures" : ${ARCHITECTURES},
      "TrustedGPG" : "${GPG}"
    },
__ENDL
}

removeLastComma()
{
    perl -e '$t=join("", <STDIN>); $t=~s/,$//; print $t;'
}


###############################################################
REPO='debian'
SUITES='conf/debian.suites'
URL='http://deb.debian.org/debian/'
COMPONENTS='main contrib non-free'
ARCHITECTURES='[ "i386", "amd64" ]'
GPG='./gpg/debian.gpg'

echo "[" >$SUITES
for suite in jessie stretch wheezy; do
  suiteEntry ${suite}
  for special in backports updates proposed-updates; do
    suiteEntry ${suite}-${special}
  done
done | removeLastComma >>$SUITES
echo "]" >>$SUITES


###############################################################
REPO='ubuntu'
SUITES='conf/ubuntu.suites'
URL='http://archive.ubuntu.com/ubuntu/'
COMPONENTS='main restricted universe multiverse'
ARCHITECTURES='[ "i386", "amd64" ]'
GPG='./gpg/ubuntu.gpg'

echo "[" >$SUITES
for suite in trusty xenial artful bionic; do
  suiteEntry ${suite}
  for special in backports proposed security updates; do
    suiteEntry ${suite}-${special}
  done
done | removeLastComma >>$SUITES
echo "]" >>$SUITES

Configuring apt-repos
=====================

The configuration files for apt-repos are seached in different places on a system, dependent on how these files should be shared with other users. This is conThe following folders are searched for:

The *suites*-file can live in the following places:
* /etc/apt-repos/suites - default location if not overridden by next one
* $HOME/.apt-repos/suites - allows to override the system wide default


Each repository URI is mapped to a shortname. E.g. 'http://de.archive.ubuntu.com/ubuntu/' to the much more simple form "ubuntu:". We just add the suite-name and are now able to address the above example repository/suite combinations with very short names, e.g. "ubuntu:xenial", "ubuntu:xenial-updates" or "ubuntu:xenial-security". From now on will call such a short name 'suite-id'.

One or more apt-repos specific configuration files describe the mappings from suite-id's to SourcesList-entries, e.g.

    [
       {
          "Suite" : "ubuntu:xenial",
          "SourcesList" : "deb http://de.archive.ubuntu.com/ubuntu/ xenial main restricted universe multiverse"
          "DebSrc" : true,
          "Architectures" : [ "i386", "amd64" ]
       },
       {
          "Suite" : "ubuntu:xenial-security",
          "SourcesList" : "deb http://security.ubuntu.com/ubuntu xenial-security main restricted universe multiverse"
          "DebSrc" : true,
          "Architectures" : [ "i386", "amd64" ]
       }
    ]

More information about how to configure apt-repos can be found in docs/Configuration.md. 


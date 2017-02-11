Short Description
=================

Show information about binary and source packages in multiple (independent) apt-repositories utilizing libapt / python-apt/ apt_pkg without the need to change the local system and it's apt-setup.

Long Description
================

This tool is aimed for people that extensively work with multiple apt-repositores, e.g. developers of an own debian based software distribution, debian package maintainers or debian users who just want to get an overview about packages that are provided in various apt-repositories and suites. Similar to the well known tools 'apt-cache (show|policy|search)', 'apt-get (update)', 'dpkg (-l)' it prints information about binary packages and source packages that live in apt-repositories. In contrast to these tools that typically work on a concrete local host with a concrete local apt-setup, this tool allows to inspect multiple indipendent apt-repositories and suites without coupeling the local system to these repositories.

The Use-Cases
=============

As known from /etc/apt/sources.list-Files, Apt-Repositories are uniquely identified by an URI pointing to the root of a file system structure that is typically exported per http. Each repository can provide packages for multiple suites, components and architectures. A sources.list definition can contain multiple repository/suite/component combinations that are logically merged into one apt-setup that is valid for the concrete local system. On my Ubuntu-System, for example the following apt repository/suite/component combinations are currently active:

    deb http://de.archive.ubuntu.com/ubuntu/ xenial main restricted
    deb http://de.archive.ubuntu.com/ubuntu/ xenial-updates main restricted
    deb http://de.archive.ubuntu.com/ubuntu/ xenial universe
    deb http://de.archive.ubuntu.com/ubuntu/ xenial-updates universe
    deb http://de.archive.ubuntu.com/ubuntu/ xenial multiverse
    deb http://de.archive.ubuntu.com/ubuntu/ xenial-updates multiverse
    deb http://security.ubuntu.com/ubuntu xenial-security main restricted
    deb http://security.ubuntu.com/ubuntu xenial-security universe
    deb http://security.ubuntu.com/ubuntu xenial-security multiverse

With the help the tool apt-cache it is now possible to retrieve information about packages provided by the above apt-setup. There is currently no simple way to retrieve information about packages in other repository/suite/component constellations without modifying the local apt-setup. This means that it is not easily possible to e.g. show the list of packages provided by an old ubuntu-suite like trusty.

The following use-cases are addressed by this project:

* People that create their own debian based software distribution want to inspect the own apt-repositories independently from the local machine setup. Typically queries or tasks could be:
    * List binary packages and versions in a repository/suite combination
    * List about binary packages and versions provided for a particular architecture.
    * List about binary packages and versions provided in a particular component
    * Compare the versions of a binary package in different suites
* As a debian package developer you might want to 
    * Show detailed package information for foreign repository/suite combinations similar to the information that 'apt-cache show' prints for local apt-setups.
    * Map from a binary package to the source package that it was created from or vice versa.
    * Download foreign binary or source packages to do something with them on the local system.
* Maybe any debian users want to check if a particular package version is available in a particular foreign PPA or backports repository.

The Solution
============

Each repository URI is mapped to a shortname. E.g. 'http://de.archive.ubuntu.com/ubuntu/' to the much more simple form "ubuntu:". We just add the suite-name and are now able to address the above example repository/suite combinations with very short names, e.g. "ubuntu:xenial", "ubuntu:xenial-updates" or "ubuntu:xenial-security". From now on will call these short names 'suite-selectors'.

A json file describes the mappings from suite-selectors to SourcesList-entries.

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

The *suites*-file can live in the following places:
* /etc/apt-repo/suites - default location if not overridden by next one
* $HOME/.apt-repo/suites - allows to override the system wide default

A new command line tool 'apt-repo' prints information about the packages in these repositories. Analogue to the nomenclature of 'apt-cache', 'apt-repo' provides various sub commands:

*   *apt-repo ls*: query for packages that meets particular criteria and show the results as a list
*   *apt-repo show*: show detailed information about selected debian packages analogue to 'apt-cache show'
*   *apt-repo dget*: download particular packages
*   *apt-repo sourcesList*: print the SourcesList entries that would be generated for a particular suite-selectors.

We use the suite-selectors to describe in which repository/suite combinations we want to search for a particular query.

TODO: more about suite-selectors

Each time a particular repository/suite combination is scanned, apt-repo checks if there are new Packages-Files available in the repository and downloads the Packages-Files if necessary into a local cache.

A new python module LibAptRepo.py allows us to access the information in the local cache. Also the command line interface *apt-repo* uses this library. This way we can easily access package information not only in *apt-repo* but also in other custom python modules.

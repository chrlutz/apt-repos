Short Description
=================

Show information about binary and source packages in multiple (independent) apt-repositories utilizing libapt / python-apt/ apt_pkg without the need to change the local system and it's apt-setup.

Long Description
================

This tool is aimed for people that extensively work with multiple apt-repositores, e.g. developers of an own debian based software distribution, debian package maintainers or debian users who just want to get an overview about packages that are provided in various apt-repositories and suites. Similar to the well known tools 'apt-cache (show|policy|search)', 'apt-get (update)', 'dpkg (-l)' it prints information about binary packages and source packages that live in apt-repositories. In contrast to these tools that typically work on a concrete local host with a concrete local apt-setup, this tool allows to inspect multiple indipendent apt-repositories and suites without coupling the local system to these repositories.

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

With the help the tool apt-cache it is now possible to retrieve information about packages provided by the above apt-setup. There is currently no simple way to retrieve information about packages in other repository/suite/component constellations without modifying the local apt-setup. This means that it is not easily possible to e.g. show the list of packages provided by an older ubuntu-suite like trusty.

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
* Maybe a debian user wants to check if a particular package version is available in a particular foreign PPA or backports repository.

The Solution
============

Each repository URI is mapped to a shortname. E.g. *http://de.archive.ubuntu.com/ubuntu/* to the much more simple form "ubuntu:". We just add the suite-name and are now able to address the above example repository/suite combinations with very short names, e.g. "ubuntu:xenial", "ubuntu:xenial-updates" or "ubuntu:xenial-security". From now on will call such a short name *suite-id*.

One or more apt-repos specific configuration files describe the mappings from suite-id's to SourcesList-entries, such as

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
       },
       {
          "Suite" : "kubuntu-backports:xenial",
          "SourcesList" : "deb http://ppa.launchpad.net/kubuntu-ppa/backports/ubuntu xenial main"
          "DebSrc" : true,
          "Architectures" : [ "i386", "amd64" ]
       }
       
    ]

There are various ways to define single suites or multiple suites from an apt-repository. Apt-repos also has the ability to scan existing apt-repositories to dynamically find and map contained suites to suite-id's. More information about how to configure apt-repos can be found in [docs/Configuration](docs/Configuration.md).

A new command line tool *apt-repos* prints information about the packages in these repositories. Analogue to the nomenclature of *apt-cache*, *apt-repos* it provides various sub commands:

*   **apt-repos list|ls**: Query for binary packages that meet particular criteria and show the results as a list
*   **apt-repos sources|src**: Query for source packages that meet particular criteria and show the results as a list
*   **apt-repos show**: Show detailed information about selected debian packages analogue to 'apt-cache show'
*   **apt-repos suites**: List registered suites and their corresponding 'apt/sources.list' entries that would be generated in the background for particular suite-selectors.
*   **apt-repos dsc**: Print the URLs of dsc-files for particular source packages. The output could e.g. be combined with the well known 'dget … URL' from the devscripts package

We use so called *suite-selectors* to describe in which repository/suite combinations we want to search for a particular query. The following ways of selecting suites are possible:

* Select a single suite by a full qualified **suite-id**: e.g. "ubuntu:xenial" selects exactly one suite as specified in the above suite configuration
* Select all suites in a repository, specified by the **reporitory-prefix** (which ist the first part of the suite-id including the colon): e.g. "ubuntu:" selects all defined ubuntu-suites --> ubuntu:xenial and ubuntu:xenial-security
* Select multiple suites by a **suite-name** (the part after the colon, only): e.g. "xenial" would select the suites "ubuntu:xenial" and "kubuntu-backports:xenial"
* Select multiple suites with the same **tag**: Each Suite can be assigned one or more tags used to group suites that logically belong together. We could for example assign a tag "production" to all three above specified suites and select these suites with the selector "production:". Please see [[docs/Configuration]] on how to set tags.

Each time a particular repository/suite combination is scanned, apt-repos checks if there are new Packages-Files available in the repository and downloads the Packages-Files if necessary into a local cache.

A python module python3-apt-repos (provided in this git-repository) allows us to access the information in the local cache. Also the command line interface *apt-repos* uses this library. This way we can easily access package information not only in *apt-repos* but also in other custom python modules.

State
=====

Current State:

* The command line interface (CLI) *apt-repos* exists and provides the above mentioned subcommands.
* There is a python3 library *python3-apt-repos* which provides access to the
  apt-repos configuration data and the scanned packages from custom python3 code. This
  way it can be reused by other components / use-cases than the CLI apt-repos, too.
  Parts of the library / API can not yet be considered stable (while others are)!
* There are various examples in the 'test'-folder. This folder contains a very simple
  test mechanism that already contains some testcases with a quite good (but of course
  still improvable) test coverage. We have unittests and integration tests
  (here called 'clitests') to test the command line interface.
* There's a debian packaging mechanism to create the debian-packages *apt-repos* (the CLI)
  and *pyton3-apt-repo* (the library package)
* There are manpages for the CLI apt-repos and it's subcommands
* The tool has already been proven to reliaby support a complex development process.


Contributions from interrested people via patches or pull requests are very welcome.

License
=======

Everything there is licensed under LGPL version 2.1 or any later version.

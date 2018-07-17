Configuring apt-repos
=====================

Apt-repos is configured by simple json files. Two different types of files are supported: *.suites*-files and *.repos*-files. Both file types are there to specify apt-repositories and their suites, but both work slightly on different levels:

* **.suites-files** are the "low-level" way of describing suites (in fact this type was the first type implemented in apt-repos). It requires you to define one explicit entry for each suite, containing all the information required for using the suite.
* **.repos-files** are more higher-level. In these files, it is possible to just specify repository URLs and only a small amount of metadata. Apt-repos is able to scan these repositories and to automatically derive *suite*-entries for found suites.

The syntax and supported Tags for *.suites*- and *.repos*-files are described in the subsequent sections.

Apt-repos searches for configuration files in a fixed order in either a user-specific folder or in a system folder. This allows us to share common configuration files beween users but also to augment or override particular settings for user-specific needs. The following folders are searched for configuration files in the given order:

* **$HOME/.config/apt-repos**: The XDG conform folder for user specific config files. This folder should be preferred for your user specific configuration.
* **$HOME/.apt-repos**: The 'old' folder for user specific config files - support for this folder is deprecated.
* **/etc/apt-repos**: The folder for the host global (shared) configuration.

Apt-repos interprets all files combined from these folders and ending with ".suites" or ".repos" in alphabetical order. You are free to name the first part (before .suites or .repos) however you want. Once a file with a particular filename is read in a folder, it is ignored in a latter read folder. This way it is possible to override global settings. It is also possible to use the (unchanged) global configuration and to just add custom suites to files specified with disjunct filenames.

As an alternative, apt-repos could be called with the command line switch **--basedir** that allows us to define a basedir to look for config files. If this basedir is defined, other folders will not be read. This feature is also available within the apt_repos library and called by `apt_repos.setAptReposBaseDir(basedir)`.

Examples for *.suite*- and *.repos*-files can be found in the files [test.suites](../test/test.suites) and [test.repos](../test/test.repos) in the test folder.

## Syntax and supported Keywords of *.suites-files

A *.suites file consist of a list of *suite_descriptions*. It's general syntax is:

    [
        suite_description1,
        "---- optional string-argument that works as an optical separator ----",
        suite_description2,
        ...,
        suite_descriptionN
    ]

Each *suite_description* describes the properties of a suite within a repository. 

The **order** in which *suite_descriptions* are defined plays an important role, too: In the apt-repos subcommands **suites**, **list|ls**, **sources|src** this order defines the order in which the list output for the column "Suite" is sorted. Please note that in apt-repos a list output is always sorted in the column-order from left to right. This means that if the default columns (Package, Version, Suite, Arch, Section, Source) are displayed, the list output is in the first place ordered by the Package name, in second place by the Version and in the third place by the suite in the above defined order. The idea behind this is that there is typically a kind of "lifecycle" in which a package of a particular version occurs in different suites. Let's take the example of a distribution maintainer that creates a custom distribution based on an upstream distribution like ubuntu or debian. In this case, a package (in a particular version) might first occur in the upstream repository. Then the package is put into a development or staging repository from the custom distribution maintainer and after successfull tests, the package is put into a deployment or production repository. The lifecycle in this case would be "Upstream -> dev/staging -> deploy/production". It would be helpful to model this logic in the apt-repos list output, too. This could be done by the order of *suite_desctiption*s in the .suites-file: First we define all upstream repositories/suites, then we define the development/staging suites and then the deployment/production suites. For the apt-repos subcommand **dsc** this order is intentionally reversed, because working with dsc-files typically means that custom dsc-files (if available) should be preferred over the dsc-file from upstream sources. 

This order is also inherent for *RepoSuite*-Objects from the *apt_repos* library and e.g. returned by the command `sorted(apt_repos.getSuites(suiteSelector))`.

A *suite_description* is a json object (something between "{ }") or in other words a set of key-value pairs, e.g.

    {
        "Suite" : "ubuntu:xenial",
        "Tags": [ "production", "somethingElse" ],
        "SourcesList" : "deb http://de.archive.ubuntu.com/ubuntu/ xenial main restricted universe multiverse"
        "DebSrc" : true,
        "Architectures" : [ "i386", "amd64" ]
    }

The following Keys are read bei apt-repos. It is possible to use custom keywords which will be simply ignored.



### Suite (mandatory)

The unique suite-id. This field is aimed to be a short human readable identifier of a suite. It consist of the following parts "*repository*:*suitename*". For both parts *repository* and *suitename* you are free to choose the name you like - in particular these names don't need to be connected to the physical repository- or suitenames defined in the entry *SourcesList*. However please consider that the *repository* part can be used to select multiple suites with one suite-selector. It is suggested to use the *repository* part to define a group of suites that are (at least logically) parts of the same repository. The *suitename* part would be in most cases identical to the *suitename* used in the SourcesList-Entry, but could also differ in order to be able to produce uniq suite-id's.

### Tags (optional)

Tags are another way of grouping suites into logical groups and to select particular suites with one single suite-selector `"<tag>:"`. The value for Tags is expected to be a list of one or more strings - each string is one tag. This means a valid Tag(s) definition could be for example:

    "Tags": [ "tag1", "tag2", ... ]

### SourcesList (mandatory)

The SourcesList entry is an entry in the form that is typically used in the file /etc/apt/sources.list. See *man sources.list* (available on most linux systems) for more information and it's correct definition. A SourcesList entry typically consists of the following elements:

    deb <Repository-URL> <suitename> <space_separated_list_of_components>

This contains all information really needed to define a particular repository, the corresponding suite and the components that needs to be considered.
Apt-repos will use this information to create a shadow sources.list file in the background to query the content of the suite.

### DebSrc (optional)

If provided, this key expects a boolean value - *true* or *false*. If not provided, it is defaulted to *false*. This value describes if a suite contains source packages. If this value is *true*, this would have the same effect as the list entry

    deb-src <Repository-URL> <suitename> <space_separated_list_of_components>

in the created shadow sources.list file (where the parts *Repository-URL*, *suitename* and *space_separated_list_of_components* are taken from the defined SourcesList entry).

### Architectures (mandatory)

The Architectures key expects a list of strings (of architectures) to consider during suite queries, e.g.

    [ "arch1", "arch2", ... ]

### TrustedGPG (optional)

With this key it is possible to specify the path to a file containing the public key for which the Release-File of the suite needs to be signed. This is used to validate the suite and to ensure the suite is not manipulated by a third party. The value needs to be the path to a file on the local machine - either as an absolute path or as a path relative to the folder that contains the *.suites-file. If this key is not specified, the validation is skipped.

## Syntax and supported Tags of *.repos-files

A *.repos file consist of a list of *repo_descriptions*. It's general syntax is:

    [
        repo_description1,
        "---- optional string-argument that works as an optical separator ----",
        repo_description2,
        ...,
        repo_descriptionN
    ]

Each *repo_description* describes the properties of a repository which might contain multiple suites. *repo_descriptions* are interpreted by apt-repos as a convenient layer to reduce configuration effort. This means that a *repo_description* is used as a kind of template to auto generate (invisible) *suite_descriptions* in the background.

As in *.suites*-files, the **order** in which *repo_descriptions* are defined is important as well (see above). For suites derived from *repo_description*s, the following rules are applied:

* *repo_descriptions* are scanned in the order as defined in the *.repos* file, but after *.suite*-files (so suites defined in *.repos*-files always have a higher order than suites from *.suites*-files).
* Suites derived from a *repo_description* are ordered in alphabetical order by their suitename.

A *repo_description* is a json object (something between "{ }") or in other words a set of key-value pairs. The following example shows all available keys, but typically one would only specify the really required keys (the most keys are optional):

    {
        "Repository" : "Main Debian Repository",
        "Suite" : "debian:{Suite}",
        "Tags" : [ "stable" ],
        "Url" : "http://deb.debian.org/debian/",
        "Suites" : {
            "stretch": { "Tags" : [ "test" ] },
            "stretch-backports": {},
            "stretch-updates": { "Tags" : [ "test2" ] }
        },
        "Scan" : false,
        "ExtractSuiteFromReleaseUrl": true,
        "Architectures" : [ "i386", "amd64" ],
        "TrustedGPG" : "./gpg/debian.gpg"
    }

This is the detailed description of the supported Keys (Again it is possible to use custom keywords which will be simply ignored):

### Repository (optional)

This field aims to be a human readable short description of the repository. Thus the field is optional, it is still suggested to set a Repository-field. This would make the output of (the user visible) "Scanning Repository ..." lines easy readable. It would also make reading *.repos* files easier and helps to distinguish *.suites* and *.repos* files by just looking at the content.

### Suite (mandatory)

The unique suite-id used as a human readable identifier for the generated *suite_description*s (see section 'Suite' above).

In order to derive unique suite-id's for all suites of a repository, **the Suite definition in a *.repos-file* needs to contain a variable that expresses the dynamic part of the suite-id**. This means a Suite definition inside a *.repos-file* typically looks like "*constant*{*variable*}", where the *constant* is a string that has to contain a colon ":" and *variable* needs to be one of the following values:

* **Suite**: This variable represents the suitename as defined by the keyword *Suite* in the corresponding Release-File of the suite in the apt-repository
* **Codename**: This variable represents the codename as defined by the keyword *Codename* in the corresponding Release-File of the suite in the apt-repository
* **Label**: This variable represents the label as defined by the keyword *Label* in the corresponding Release-File of the suite in the apt-repository
* **FromReleaseUrl**: This variable represents a suitename that is extracted from the URL of the Release-File. This means that if the corresponding Release-file is reachable under the URL "http://deb.debian.org/debian/dists/jessie/Release", the suitename is extracted as the string between "dists/" and "/Release", which is "jessie" in this case.
* **FromSuites**: This variable represents the suitenames (in the below example "suitename1" and "suitename2") as defined in the list of suites under the key *Suites* in this *repo_description*. This variable could only be used together with the key *Suites* and is undefinded if the key is missing. 

"*constant*{*variable*}" together form a suite-id for the generated *suite_description*s that as in *.suites-files* logically consists of the two parts "*repository*:*suitename*". 

This allows you to define your own way of naming the resulting suite-ids. The most important thing is to be aware that physical codenames in real existing repositories could be identical for different repositories (e.g. The ubuntu suite "bionic" has the same codename in the main repository and in the backports repository).

### Url (mandatory)

This is the Repository-Url that describes the location of the repository. A Repository-Url is typically the URL under which the folders *dists* and *pool* are found.

### Tags (optional)

Tags are another way of grouping suites into logical groups and to select particular suites with one single suite-selector `"<tag>:"`. The value for Tags is expected to be a list of one or more strings - each string is one tag. Tags defined in this field are **global for all** suites derived from the *repo_description*.

If you would like to set tags on particular suites only, please have a deeper look at the description of the *Suites* keyword.

### Suites (optional)

It is not necessary to define the suites inside a repository. apt-repos could automatically scan the repository for contained suites. But using this Key, it is possible to explicitely define suites. This could have the following advantages:

* It's possible to just select particular suites you are interested in (ignoring other suites also defined in the repository).
* Scanning a repository could be accelerated by defining suites (because we don't have to build a repository index).
* It makes it possible to add suite specific tags (and maybe more metadata in future).

The Keyword Suites expects either a list of strings (=suitenames) or a set of key/value pairs in which the suitenames are the keys. This Suites could have the following values:

    [ "suitename1", "suitename2", ... ]

or

    {
        "suitename1": { "Codename":"codename" },
        "suitename2": {},
        ...
    }

The first version allows us to just select particular suites, while the second version allows us to select particular suites plus additional metadata inside the curly brackets after the suitename. 

At the moment only the definition of suite specific *Tags*-Keywords is supported. Please have a look at the above *Tags*-definition and syntax for more details.

### Scan (optional)

This optional Keyword expects the boolean values `true` or `false` and controls whether this repository should be automatically scanned for suites. If this option is not specified, it defaults to `false`. If this option is set `true`, apt-repos would automatically scan the repository for contained suites. For all suites found in this repository a *suite_description* would be generated.

Note: This option can be combined with the second version of the above *Suites*-Keyword to add suite specific metadata to particular suites. In other constellations it would not make sense to combine *Scan* and *Suites*, because `Scan: true` would always override a specified selection.

### Architectures (optional)

For suites generated via *repo_descriptions*, the supported architectures of a suite are automatically extracted from the suites *Release* file. Thats the reason why this field is optional for *repo_descriptions* while this field is mandatory for the (more low level) *suite_descriptions*. But still in some cases it could be useful to specify the architectures explicitly, e.g to suppress some curious architectures that you are not interested in.

As above, the Architectures key expects a list of strings (of architectures) to consider during suite queries, e.g.

    [ "arch1", "arch2", ... ]

If such a list is defined, only architectures from this list will be considered. If an achitecture is specified in this list, but not listed in the *Release*-file, this architecture would not be considered.

### TrustedGPG (optional)

If specified, the value of TrustedGPG is directly passed through to the generated *suite_description*s - for more details, please have a look at the corresponding Key-definition for *.suites-files.

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

Apt-repos interprets all files in these folders ending with ".suites" or ".repos" in alphabetical order. You are free to name the first part (before .suites or .repos) however you want. Once a file with a particular filename is read in a folder, it is ignored in a latter read folder. This way it is possible to override global settings. It is also possible to use the (unchanged) global configuration and to just add custom suites to files specified with disjunct filenames.

## *.suites-files - Syntax and supported Keywords

A *.suites file consist of a list of suite-descriptions. It's general syntax is:

    [
        suite_description1,
        "---- optional string-argument that works as an optical separator ----",
        suite_description2,
        ...,
        suite_descriptionN
    ]

A suite_description is a json object (something between "{ }") or in other words a set of key-value pairs, e.g.

    {
        "Suite" : "ubuntu:xenial",
        "Tags": [ "production", "somethingElse" ],
        "SourcesList" : "deb http://de.archive.ubuntu.com/ubuntu/ xenial main restricted universe multiverse"
        "DebSrc" : true,
        "Architectures" : [ "i386", "amd64" ]
    }

The following Keys are supported. It is possible to use custom keywords not in this list inside a suite_description - they will be simply ignored by apt-repos.

### Suite (mandatory)

The unique suite-id. This field is aimed to be a short human readable identifier of a suite. It consist of the following parts "*repository*:*suitename*". For both parts *repository* and *suitename* you are free to choose the name you like - in particular these names don't need to be connected to the physical repository- or suitenames defined in the entry *SourcesList*. However please consider that the *repository* part can be used to select multiple suites with one suite-selector. It is suggested to use the *repository* part to define as a group of suites that are (at least logically) parts of the same repository. The *suitename* part would be in most cases identical to the *suitename* used in the SourcesList-Entry, but could also differ in order to be able to produce uniq suite-id's.

### Tags (optional)

Tags are another way to group suites into a logical group and to select all of these suites with one single suite-selector "*tag*:". The value for Tags is expected to be a list of one or more strings - each string is one tag. 

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

The Architectures key expects a list of strings (of architectures) to consider during suite queries.

### TrustedGPG (optional)

With this key it is possible to specify the path to a file containing the public key for which the Release-File of the suite needs to be signed. This is used to validate the suite and to ensure the suite is not manipulated by a third party. The value needs to be the path to a file on the local machine - either as an absolute path or as a path relative to the folder that contains the *.suites-file. If this key is not specified, the validation is skipped.

## *.repos-files - Syntax and supported Tags
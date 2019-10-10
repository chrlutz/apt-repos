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

Apt-repos interprets all files combined from these folders ending with the suffixes ".suites" or ".repos". You are free to name the first part (before the suffix) however you want. The files are sorted by their filename without suffix in alphabetical order. Once a file with a particular filename is read in a folder, it is ignored in a latter read folder. This way it is possible to override global settings. It is also possible to use the (unchanged) global configuration and to just add custom suites to files specified with disjunct filenames. If necesssary, it is also possible to override just single sections of a file using the key *Oid* (see description below).

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

With this key it is possible to specify the path to a file containing the public key with which the Release-File of the suite is signed. This is used to validate the suite and to ensure the suite is not manipulated by a third party. The value needs to be the path to a file on the local machine - either as an absolute path or as a path relative to the folder that contains the *.suites-file. Even if the Key is marked as "optional" here, it is strongly recommened to provide this value. If this key is not specified, the default settings from the local system will be used and there is no guarantee that these will work for others and different systems (e.g. ubuntu vs. debian) as well. It would be very probably to get validation errors during the scan.

### Oid (optional)

This key *Oid* (standing for "Object / Override ID") is optional and allows you to define a uniq name for the *suite_description*. Once this name is defined, it is possible to override single key/value pairs of this *suite_description* by later read config-files, referring the same *Oid* in their *suite_description*. Example:

Lets assume there's a config file "some.suites" with the following content:

    [
        {
            "Oid" : "my_suite_definition",
            "Suite" : "ubuntu:xenial",
            "Tags": [ "production", "somethingElse" ],
            "SourcesList" : "deb http://de.archive.ubuntu.com/ubuntu/ xenial main restricted universe multiverse"
            "DebSrc" : true,
            "Architectures" : [ "i386", "amd64" ]
        }
    ]

It is now possible to add a file called "some_overrides.suites" that changes single settings of the above configuration:

    [
        {
            "Oid" : "my_suite_definition",
            "Tags": [ "myowntag" ]
        }
    ]

This configures the suite "ubuntu:xenial" as usual, but their *Tags* will be only `[ "myowntag" ]` instead of the previous *Tags* setting.

**Note:** this works as the file "some_overrides.suites" is read after the file "some.suites" (because files are ordered by their filename without suffix). Using the string *_overrides* inside the name of the second file is recommended as a kind of convention, but any other filename sorted after the first file would also have the same effect.

### Description (optional)

This field aims to be a human readable short description of the suite or underlying apt-repository.


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
* Suites derived from a *repo_description* are ordered in the following way:
    * if the key *Suites* is given, the order as defined in the list under the key *Suites* is used
    * if *Scan* is used, suites are added in alphabetical order by their suitename
    * in case of a combination of *Suites* and *Scan*, suites derived from *Suites* are first added, then scanned suites.

A *repo_description* is a json object (something between "{ }") or in other words a set of key-value pairs. The following example shows all available keys, but typically one would only specify the really required keys (the most keys are optional):

    {
        "Repository" : "Main Debian Repository",
        "Prefix" : "debian",
        "Tags" : [ "stable" ],
        "Url" : "http://deb.debian.org/debian/",
        "Suites" : [
            { "Suite" : "stretch", "Tags" : [ "test" ] },
            "stretch-backports",
            { "Suite" : "stretch-updates", "Tags" : [ "test2" ] }
        ],
        "Scan" : false,
        "ExtractSuiteFromReleaseUrl": true,
        "Architectures" : [ "i386", "amd64" ],
        "TrustedGPG" : "./gpg/debian.gpg"
    }

This is the detailed description of the supported Keys (Again it is possible to use custom keywords which will be simply ignored):

### Repository (optional)

This field aims to be a human readable short description of the repository. Thus the field is optional, it is still suggested to set a Repository-field. This would make the output of (the user visible) "Scanning Repository ..." lines easy readable. It would also make reading *.repos* files easier and helps to distinguish *.suites* and *.repos* files by just looking at the content.

### Prefix (mandatory)

The prefix is mandatory and describes the **first part of the suite-id** for the generated *suite_description*s (see section 'Suite' above). Please note that a suite-id logically consists of the two parts "*repository*:*suitename*". The prefix could represent the *repository* part, but it could also represent a prefix for the *suitename*-part. See the following examples:

* In the above *repo_description*, the Prefix "debian" is equivalent to the *repository* part. If the prefix does not contain a colon ":", apt-repos would automatically add `":<suitename>"`, where `<suitename>` is the name of the suite as physically defined in the suite's Release-File. This means suites with this prefix would automatically get the following suite-ids: *debian:stretch*, *debian:stretch-backports* and so on.
* A Prefix could also contain a colon ":". Let's take the example of the Prefix "ubuntu:backports-". In this case, the physical `<suitename>` will be added without a colon, so that resulting suite-ids could be for example *ubuntu:backports-xenial*, *ubuntu:backports-bionic* and so on.

This allows you to find your own way of naming your suite-ids. The most important thing is to be aware that physical suitenames in real existing repositories could be identical for different repositories (e.g. The ubuntu suite "bionic" has the same suitename in the main repository and in the backports repository). apt-repos needs uniq suite-id's. That's why you would have to find a good prefix.

### Url (mandatory)

This is the global Repository-Url that describes the location of the repository. A Repository-Url is typically the URL under which the folders *dists* and *pool* are found.

This setting is used for all Suites of the repository if there is no suite specific Url-Key provided (see below).

For Urls defined in *.repos-files, there is also a simple kind of variable replacement implemented. The following variables are currently supported:

* *{PWD}*: is replaced by the current working directory of the parent process that calls apt-repos. This replacement is only done for file-Urls (Urls starting with "file://"). Example: Use `"Url" : "file://{PWD}/repo"` to define a repository in the folder "repo" relative to the current working directory.

### Tags (optional)

Tags are another way of grouping suites into logical groups and to select particular suites with one single suite-selector `"<tag>:"`. The value for Tags is expected to be a list of one or more strings - each string is one tag. Tags defined in this field are **global for all** suites derived from the *repo_description*.

If you would like to set tags on particular suites only, please have a deeper look at the description of the *Suites* keyword.

### Suites (optional)

It is not necessary to define the suites inside a repository. Using the key *Scan*, apt-repos could automatically scan the repository for contained suites. But with this Key, it is possible to explicitely define suites to be resolved from this repository. This could have the following advantages:

* It's possible to just select particular suites you are interested in (ignoring other suites also defined in the repository).
* Scanning a repository could be accelerated by defining suites (because we don't have to build a repository index).
* It makes it possible to add suite specific tags.

The Keyword Suites expects a list of suites, either identified by strings in which case the string is just the *suitename* or by sets of key/value pairs in which the key "Suite" represents the *suitename*:

    [ 
        "suitename1", 
        "suitename2",
        "--- A string starting with three dashes is interpreted as a separator and is ignored ---",
        { "Suite" : "suitename3", ... },
        { "Suite" : "suitenameN", ... },
        ...
    ]

The first two list entries allow us to just select particular suites, while the last two list entries allow us to select particular suites and set suite specific metadata (inside the curly brackets after the suitename). The *suitename* is expected to be the name of a suite that is available in the repository. As additional, suite specific metadata, the following Keys are supported:

* **Tags**: Besides the global *Tags* for the repository (see above) this Key could be used to define suite specific tags that will be use additionally. Please have a look at the above *Tags*-definition and syntax for more details.
* **Url**: If this Key is set, a suite specific Url will be created by combining the global Repository-Url (as base-Url) with this value. The resulting Url must point to a Repository in which typically the folders *dists* and *pool* can be found. Using this key it is possible to define a *repo_description* that logically acts as one repository but essentially consists of multiple independent apt repositories sharing the same base-Url.
* **Codename**: This optional keyword defines a suite specific folder (of the apt repository) under `dists` in which we look for the particular suite's Release-File. If this value is set, it has precedence before the common *Codename* key that could be also used on *repo_description*-level.
* **Trusted**: Suite specific Override of the `Trusted`-Setting from the *repo_description*-level.

### Codename (optional)

This optional key (on *repo_description*-level) allows to set a common codename for all suites defined in the above key *Suites*. It is only used if there is no suite specific *Codename* set. If there is no suite specific *Codename* and no common codename defined, the codename is automatically the (suite specific) *suitename*. This option makes only sense in combination with *Suites*:

The *Codename* describes the folder (of the apt repository) under `dists` in which we look for a particular suite's Release-File.

### Scan (optional)

This optional Keyword expects the boolean values `true` or `false` and controls whether this repository should be automatically scanned for suites. If this option is not specified, it defaults to `false`. If this option is set `true`, apt-repos would automatically scan the repository for contained suites. For all suites found in this repository a *suite_description* would be generated.

Note: This option can be combined with the second version of the above *Suites*-Keyword to add suite specific metadata to particular suites. In other constellations it would not make sense to combine *Scan* and *Suites*, because `Scan: true` would override any selections.

### ExtractSuiteFromReleaseUrl (optional)

As described for the Key *Prefix*, the suite-id of the generated *suite_description* would normally be build as a combination of `<Prefix><physical_suitename>`, where the *physical_suitename* is the name that is specified in the suites "Release"-file. This could be a problem with some repositories that don't use the "ubuntu way of naming suites".

For example debian has this concept of *oldstable*-, *sid*-, *stable*-, *unstable*- and *testing*-suites in which the *physical_suitename* is not one of the Known-Releasenames *jessie*, *stretch* or *wheezy*, but one of the "rolling" names *oldstable*, *stable* and so on. To ensure our generated suite-id's are build of `<Prefix><Known_Releasename>`, the Key *ExtractSuiteFromReleaseUrl* could be set `true`. This would extract the releasename from the URL of the Release-File (e.g. "http://deb.debian.org/debian/dists/jessie/Release") and use *jessie* instead of it's (current) *physical_suitname* *oldstable* defined in the Release file.

### Architectures (optional)

For suites generated via *repo_descriptions*, the supported architectures of a suite are automatically extracted from the suites *Release* file. Thats the reason why this field is optional for *repo_descriptions* while this field is mandatory for the (more low level) *suite_descriptions*. But still in some cases it could be useful to specify the architectures explicitly, e.g to suppress some curious architectures that you are not interested in.

As in the example above, the Architectures key expects a list of strings (of architectures) to consider during suite queries, e.g.

    [ "arch1", "arch2", ... ]

If such a list is defined, only architectures from this list will be considered. If an achitecture is specified in this list, but not listed in the *Release*-file, this architecture would not be considered, too.

### Components (optional)

Similar to the key `Architectures`, for suites generated via *repo_descriptions*, the supported components of a suite are automatically extracted from the suites *Release* file. Adding a Components list typically just makes sense in order to specify a self-contained *repo_description* (see below).

The Components key expects a list of strings (of components) that are supported by the generated suite(s), e.g.

    [ "main", "restricted", ... ]

If such a list is defined, only components from this list will be considered. If a components is specified in this list, but not listed in the *Release*-file, this component would not be considered, too.

### TrustedGPG (optional)

If specified, the value of TrustedGPG is directly passed through to the generated *suite_description*s - for more details, please have a look at the corresponding Key-definition for *.suites-files.

### Trusted (optional)

The key *Trusted* expects a boolean value *true* or *false*. If the key is not specified, the default value is *false*. If *Trusted* is set *true*, in the generated sources.list line for the derived suites the option `[trusted=yes]` will be set. This has the effect that suites could be used even if their TrustedGPG validation fails for whatever reason.

### DebSrc (optional)

Similar to the equally named Key in *suite_descriptions*, this key expects a boolean value - *true* or *false* and describes if the generated suites contain source packages. The difference is, that in a *repo_description* this information can be automatically extracted from the Release-files of the generated suites. If this key is not specified, the automatically extracted information is used.

### Oid (optional)

For *repo_descriptions* the override-feature is also available analogue to the way it works for *suite_description*s (see above)

## Self-Contained *repo_description*s

A Self-Contained *repo_description* is a repository description (inside a *.repos-file) that contains all the information required to create *suite_description*s out of the box - without reading the repositories/suites Release-file and further repository scans. A *repo_description* is self-contained if it defines at least the following Keys:

* **Url**
* **Suites** (defining the list of suites for which we want to create *suite_description*s)
* **Architectures**
* **Components**
* **DebSrc** (both values 'true' and 'false' are possible here)

If apt-repos detects a self-contained *repo_description*, no repository scan will be performed for all suites defined in `Suites`. The usage of the "self-contained" mode is logged in debuglevel, so `apt-repos -d ...` would report about the usage.

Using the self-contained mode has the following advantages:

* a self-contained *repo_description* is processed faster
* It's possible to define suites that don't exist physically. There are some use cases in which we want to define suites event if they do not yet exist - e.g. if we want to just create those suites with parameters provided by apt-repos. Note, that this is also possible with *suite_description*s, but with self-contained *repo_description*s,
* the features of *.repos-files can be used, too. For example:
    * using the variable substitution available for file-URLs in *repo_description*s (this is not supported for the more low level *suite_description*s!)
    * defining multiple suite within one configuration block (sharing same attributes) - which is a shorter and more redundance-free form.

All the other key's (not mentioned in the above list) should behave as described, besides the following exceptions:

* **ExtractSuiteFromReleaseUrl**: It doesn't make sense to use this key in self-contained mode, since no Release file is read. Using this option would return the unchanged suite-name as specified in the `Suites` list.
* **Scan**: Together with the "self-contained"-mode, `"Scan" = true` would cause Suites in the `Suites` list to be not scanned while the repository is still scanned for other suites. This doesn't make much sense, too.
* **Codename** is ignored for all Suites defined in the `Suites`-list.

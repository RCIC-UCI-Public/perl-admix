# perl-admix
Perl and its modules RPMS created via YAML2RPM

##  Prerequisites

1. Make sure the development RPMs are installed. Follow the `Quickstart`
   section of the guide in https://github.com/RCIC-UCI-Public/yaml2rpm/blob/master/README.md

1. Check environment an unset if any of the PERL related are set. Specifically,
   ```bash
   unset PERL5LIB PERL_MB_OPT PERL_LOCAL_LIB_ROOT PERL_MM_OPT
   ```

   When these variabls are set it can change the default options for perl build
   and create an incompatibility.

##  Build Perl
These include packages perl, its environment module and a set of modules that are needed
to bootstrap building environment for using MetaCPAN::Client.

1. Download the repo
   ```bash
   git clone https://github.com/RCIC-UCI-Public/perl-admix
   ```

1. Create a directory for distribution soruces and download sources
   for perl and its bootstrap packages from CPAN.
   ```bash
   cd perl-admix/
   make download

1. Compile and install perl and ll the sets of modules for both perl versions.
   ```bash
   make buildall-parallel &> buildall.log &
   ```

   After this step, perl, perl environment module and perl modules RPMS are build
   for Perl versiosn 5.30.0 and 5.34.1 (total 400 RPMs).

   In addition, the following RPMs are created: 
   
     * perl_5.30.0-baseline-bioperl-5.30.0-1.x86_64.rpm
     * perl_5.30.0-baseline-genomics-5.30.0-3.x86_64.rpm
     * perl_5.30.0-baseline-metacpan-5.30.0-1.x86_64.rpm
     * perl_5.34.1-baseline-bioperl-5.34.1-1.x86_64.rpm
     * perl_5.34.1-baseline-genomics-5.34.1-3.x86_64.rpm
     * perl_5.34.1-baseline-metacpan-5.34.1-1.x86_64.rpm

   Each instals a single README.<group> file (group is bioperl, metacpan, genomics)
   in the perl base install directory and includes all other RPMs from 
   a corresponding group bootstrap build as dependencies.
   This allows to install all perl RPMs via simply installing these 6 RPMs (assuming yum points
   to the repo where all created perl boostrap RPMS are).

## Build groups of modules

1. A BioPerl module requires a large number of prerequisites which are not cleanly defined
   in CPAN dependencies. We provide a way to to install all checked dependencies.
   Required yaml files are in `bioperl/` and the following commands wil build and install
   all needed RPMS. This aassumes that Perl and its metacpan RPMs were already built and installed
   (they are specified in sets *meta*).
   The following command will build and install RPMS in the correct dependency order for Perl 5.30.0
   (a similar approach is for Perl 5.34.1 using set names for that version):

   ```bash
   cd yamlspecs/
   make bootstrap SET=530-bio | tee out 2>&1
   ```

   To erase all built and installed BioPerl RPMS

   ```bash
   make bioerase SET=530-bio
   ```

1. Another group of perl modules grouped into *genomics* can be built in a similar way via:

   ```bash
   cd yamlspecs/
   make bootstrap SET=530-gen | tee out 2>&1
   ```

   This set must be built after *meta* and *bio* are built and isntalled.

## Building RPMS for additional modules

The steps below outline how one can automate to a large degree creation of the
additiona perl modules RPMs. Because the perl modules do not always obey the
build process and do not provide all the dependency information, there will be
always case that will need a manual adjustment.

This usually involves overwriting requires/provides or changing the order in a buildorder file.
For the requires/provides see examples of the filters in the `metacpan/Package-Stash.yaml`
or `metacpan/ExtUtils-Helpers.yaml` or other yaml files that contain `filter_requires` or
`filter_provides` directives.

For the buildorder updates, follow error messages during RPMs build and check for errors in the
`out` file, then adjust the buildprder and rerun build RPM command.

The standard, no change outline is:

1. Create a file that lists desired perl modules names  one per line using perl module name
   schema, For example, a default file name is `desired` and the file content is:
   ```txt
   A::B
   C
   F::K
   ```

1. Before the next step make sure there is ~/.cpan/CPAN/MyConfig.pm  file
   The template for this file is generated when running  `cpan -l` command but is done interactively.
   We can generate this file before running any cpan commands via:
   ```bash
   make MyConfig.pm
   mkdir -p  ~/.cpan/CPAN/
   cp MyConfig.pm  ~/.cpan/CPAN/MyConfig.pm
   ```

1. Run a program that will query CPAN for the modules and their prerequisites
   and create yaml files for found modules. In some instances, a module will be provided
   by the `parent` modules distribution. Use perl version for which  you are building the
   the modules. For example:
   ```bash
   cd yamspecs/
   module load perl/X.Y.Z
   make desired-yaml
   ```

   Ater the execution, the following files are generated:
   - *NAME.yaml* for each desired module NAME and any found dependent modules
   - *buildorder*, shows in what order RPMS will need to be built. This file will need to be included in
     a new set-SETNAME,yaml file.
   - *versions-bootstrap*, with versions and source distro location in cpan. This file will need to be
     included in versions-SETNAME.yaml file and referenced in above set-SETNAME.yaml
   - *versions-desired*, summary information about order and versions.

1. To download all source distributions for generated yaml files one can execute
   ```bash
   make desired-download SET=SETNAME
   ```

1. To build and install RPMS for desired modules:
   ```bash
   make desired-build SET+SETNAME | tee out 2>&1
   ```
   If the build goes well a new set and its version file can be  created and  the set can be added to packages.yaml.

1. To remove built and install RPMs
   ```bash
   make desired-erase SET=SETNAME
   ```

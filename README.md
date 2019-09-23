# perl-admix
Perl and its modules RPMS created via YAML2RPM

##  Prerequisites

1. Make sure the developemnt RPMs are installed. Follow the `Quickstart`
   section of the guide in https://github.com/RCIC-UCI-Public/yaml2rpm/blob/master/README.md

1. Check environment an unset if any of the PERL related are set. Specifically, 
   ```bash
   unset PERL5LIB PERL_MB_OPT PERL_LOCAL_LIB_ROOT PERL_MM_OPT
   ```

   When these variabls are set it can change the default options for perl build 
   and create an incompatibility.

##  Build Perl
These include packages perl, its environemnt module and a set of modules that are needed
to bootstrap building environemnt for using MetaCPAN::Client.

1. Download the repo
   ```bash
   git clone https://github.com/RCIC-UCI-Public/perl-admix
   ```

1. Create a directory for distribution soruces and download sources
   for perl and its bootstrap packages from CPAN.
   ```bash
   cd perl-admix/
   make sources

   cd yamlspecs/
   make prepdownload
   ```
   After this step,  sources/ is created at the top level directory and all 
   source packages are downloaded. 

1. Compile and install perl and its bootstrap packages
   ```bash
   make prep
   make bootstrap | tee out 2>&1
   ```

   After this step, perl, perl environment module and 83 additional RPMS are build
   and they contain a basic perl with additional packages to use MetaCpan::Client module.

   In addition, a single RPM  perl_VERSION-baseline is created. It installs a single README.baseline 
   file in the perl base install directory and includes all other RPMs from bootstrap build as dependencies. 
   This allows to install all perl bootstrap RPMs via simply installing this one RPM (assuming yum points
   to the repo where all created perl boostrap RPMS are).
   
## Build BioPerl and its dependencies

1. A BioPerl module requires a large number of prerequisites which are not cleanly defined
   in CPAN dependencies. We provide a way to to isntall all checked dependencies. 
   Required yaml files are in `bioperl/` and the following commands wil build and install
   all needed RPMS. This aassumes that Perl and its baselin RPMs were already built and installed.  
   The following commadn will build RPMS in the correct  dependency order and isntall them. 
   
   ```bash
   cd yamlspecs/
   make bio
   ```

   To clean a directory after this build execute:
   ```bash
   make bioclean
   ```

   To erase all built ad installed BioPerl RPMS 
   ```bash
   make bio-erase
   ```


## Building RPMS for addiitonal modules

The steps below outline how one can automake to a large degree creation of the 
additiona perl modules RPMs. Because the perl moduesl do not always obey the 
build process and provide all the correct information, there wil be always case
that will need a manbual adjustment. 

This usually involves overwriting requires/provides or changing the order in a buildorder file.
For the requires/provides see examples of the filters in the `baseline/Package-Stash.yaml` 
or `baseline/ExtUtils-Helpers.yaml` or other yaml files that contain `filter_requires` or 
`filter_provides` directives. 

For the buildorder updates, follow error messages during RPMs build and check for errors in the
`out` file. 

The standard, no change outline is:

1. Create a file that lists desired perl modules names  one per line using perl module name
   schema, For example, a default name is `desired` and the file content is:
   ```txt
   A::B
   C
   F::K
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

   Ater the execution, files auto-NAME.yaml will be generated for all desired modules, their
   dependencies and a file `buildorder` which shows in what order RPMS will need to be built. 

1. To download all source distributions for generated yaml files one can execute
   ```bash
   make desired-download
   ```

1. To build and install RPMS for desired modules:
   ```bash
   make desired-build | tee out 2>&1
   ```

1. To remove built and isntalled RPMs 
   ```bash
   make desired-erase
   ```

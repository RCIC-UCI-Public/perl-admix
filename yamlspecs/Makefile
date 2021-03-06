# Copyright (c) 2000 - 2019 The Regents of the University of California.
# All rights reserved.	
# This includes the Generic yaml2rpm Makefile - most packaging should
# be able to use this.

# redefine BUILDALL_TARGETS
ALL_TARGETS = modules.manifest base bio genomics
MODULEYAML = perl-module
include $(YAML2RPM_HOME)/sys/Makefile

# generic settings
SHELL = /bin/bash
PERLVER = $(shell $(GENERATE) --query=version perl.yaml)
BOOTSTRAP_MODULES_FILE = modules.bootstrap
BUILD_MODULES_FILE = modules.build
MANIFEST_FILE = modules.manifest
GROUPS = metacpan bioperl genomics

# specific to metacpan/ modules
BASE_SRCVER = $(shell $(GENERATE) --query=metacpan_tarsources perl.yaml)
BASELINE = $(shell cat metacpan/buildorder)
BASELINELIST = baseline-metacpan
BASEPKGS = $(addsuffix .pkg, $(BASELINELIST))
BASERPMS = $(addprefix perl_$(PERLVER)-,$(BASELINE)) perl_$(PERLVER)-baseline-metacpan

# specific to bioperl/ modules
BIO_SRCVER = $(shell $(GENERATE) --query=bioperl_tarsources perl.yaml)
BIO = $(shell cat bioperl/buildorder)
BIOLIST = baseline-bioperl
BIOPKGS = $(addsuffix .pkg, $(BIOLIST))
BIORPMS = $(addprefix perl_$(PERLVER)-,$(BIO)) perl_$(PERLVER)-baseline-bioperl

# specific to genomics/ modules
GENOMICS_SRCVER = $(shell $(GENERATE) --query=genomics_tarsources perl.yaml)
GENOMICS = $(shell cat genomics/buildorder)
GENOMICSLIST = baseline-genomics
GENOMICSPKGS = $(addsuffix .pkg, $(GENOMICSLIST))
GENOMICSRPMS = $(addprefix perl_$(PERLVER)-,$(GENOMICS)) perl_$(PERLVER)-baseline-genomics

# specific to modules that have autogenerated yaml files
AUTOYAML = $(shell cat buildorder)
DRPMS = $(subst auto,perl_$(PERLVER),$(AUTOYAML))

# bootstrap (build and install) all perl modules in metacpan/ and bioperl/
default: MyConfig.pm modules.manifest base bio genomics

modules.manifest: 
	/bin/rm -f $(MANIFEST_FILE)
	cat modules.bootstrap.base > $(MANIFEST_FILE)
	for name in $(GROUPS); do \
	    cat $$name/buildorder >> $(MANIFEST_FILE); \
	    echo baseline-$$name >> $(MANIFEST_FILE); \
	done
	sed -i 's/^/perl_$(PERLVER)-/' modules.manifest

### all *base* targets are for modules in metacpan/
README.metacpan: metacpan/README.metacpan.in
	sed 's/@VERSION@/$(PERLVER)/' $^ > $@
	./writeVersions.sh metacpan >> $@
	
baseprep: README.metacpan 
	/bin/cp metacpan/*yaml .

basedownload: baseprep
	(cd ../sources; tar xvf sources-metacpan-$(BASE_SRCVER).tar.gz)
	for name in perl $(BASELINE); do                        \
	    distro=$$($(GENERATE) --query=tarball $$name.yaml);	\
	    echo "Checking if need to download $$distro ";      \
	    if [ ! -f ../sources/$$distro ]; then 		\
	        make download PKG=$$name; 			\
	    fi;							\
	done

base: basedownload 
	cat modules.bootstrap.base metacpan/buildorder > modules.bootstrap
	echo $(BASELINELIST) >> modules.bootstrap
	make bootstrap
	make clean baseclean 

baseclean:
	for name in $(BASELINE) $(BASELINELIST); do \
	    /bin/rm -f $$name.yaml;                 \
	done
	/bin/rm -f README.metacpan modules.build modules.bootstrap

baseerase: baseclean
	yum -y erase $(BASERPMS)
	for name in $(BASERPMS); do			\
	    rm -rf ../RPMS/x86_64/$$name-[0-9]* ;	\
	done

### all *bio* targets modules in bio/ are needed for BioPerl
README.bioperl: bioperl/README.bioperl.in
	sed 's/@VERSION@/$(PERLVER)/' $^ > $@
	./writeVersions.sh bioperl >> $@

bioprep: README.bioperl
	/bin/cp bioperl/*yaml .

biodownload: bioprep
	(cd ../sources; tar xvf sources-metacpan-$(BIO_SRCVER).tar.gz)
	for name in $(BIO); do \
	    distro=$$($(GENERATE) --query=tarball $$name.yaml);	\
	    echo "Checking if need to download $$distro "; \
	    if [ ! -f ../sources/$$distro ]; then 		\
	        make download PKG=$$name; 			\
	    fi;							\
	done

bio: biodownload 
	/bin/cp bioperl/buildorder modules.bootstrap
	echo $(BIOLIST) >> modules.bootstrap
	make bootstrap
	make clean bioclean

bioclean:
	for name in $(BIO) $(BIOLIST); do \
	    /bin/rm -f $$name.yaml; \
	done
	/bin/rm -f README.bioperl modules.build modules.bootstrap

bioerase: bioclean
	yum -y erase $(BIORPMS)
	for name in $(BIORPMS); do			\
	    rm -rf ../RPMS/x86_64/$$name-[0-9]* ;	\
	done

### all *genomics* targets modules in genomics/ are needed for genomics apps
README.genomics: genomics/README.genomics.in
	sed 's/@VERSION@/$(PERLVER)/' $^ > $@
	./writeVersions.sh genomics >> $@

genomicsprep: README.genomics
	/bin/cp genomics/*yaml .

genomicsdownload: genomicsprep
	(cd ../sources; tar xvf sources-genomics-$(GENOMICS_SRCVER).tar.gz)
	for name in $(GENOMICS); do \
	    distro=$$($(GENERATE) --query=tarball $$name.yaml);	\
	    echo "Checking if need to download $$distro "; \
	    if [ ! -f ../sources/$$distro ]; then 		\
	        make download PKG=$$name; 			\
	    fi;							\
	done

genomics: genomicsdownload 
	/bin/cp genomics/buildorder modules.bootstrap
	echo $(GENOMICSLIST) >> modules.bootstrap
	make bootstrap
	make clean genomicsclean

genomicsclean:
	for name in $(GENOMICS) $(GENOMICSLIST); do \
	    /bin/rm -f $$name.yaml; \
	done
	/bin/rm -f README.genomics modules.build modules.bootstrap

genomicserase: genomicsclean
	yum -y erase $(GENOMICSRPMS)
	for name in $(GENOMICSRPMS); do			\
	    rm -rf ../RPMS/x86_64/$$name-[0-9]* ;	\
	done

### for creating specific desired modules yamls
### see ../README.md
MyConfig.pm: MyConfig.pm.in
	sed 's%/root/%$(PWD)/%g' MyConfig.pm.in > MyConfig.pm

desired-yaml: desired
	module load perl; python depend.py desired

desired-download:
	for name in $(AUTOYAML); do \
	    distro=$$($(GENERATE) --query=tarball $$name.yaml);	\
	    if [ ! -f ../sources/$$distro ]; then 		\
	        make download PKG=$$name; 			\
	    fi;							\
	done

desired-build: desired-download
	for name in $(AUTOYAML); do					\
	    make -e -f $(THISMAKE) $$name.pkg;			\
	    make -e -C $(LOCALREPODIR) createlocalrepo; 		\
	    rpmname=$$($(GENERATE) --query=pkgname $$name.yaml);	\
	    yum -y -c $(LOCALREPODIR)/yum.conf install $$rpmname;	\
	done								\

desired-erase:
	echo $(DRPM)
	yum -y erase $(DRPMS)
	( for name in $(DRPMS); do			\
	  	rm -rf ../RPMS/x86_64/$$name-[0-9]* ;	\
	  done						\
	)
	/bin/rm buildorder

### this target creates provides/requirtes filters for each module yaml
addfilters::
	if [ -f add-filters.sh ]; then \
		/bin/bash add-filters.sh $(thismod) $(TMPBUILD) "$(GENERATE)"; \
	else \
		echo; \
	fi

debug: 
	echo "Modules: $(MODULES)"
	echo "PKGS: PKGS=$(BASEPKGS)"
	echo "PKGS: PKGS=$(BIOPKGS)"
	echo $(GENERATE)
	echo "BIO: $(BIO)"
	echo "BASELINE: $(BASELINE)"

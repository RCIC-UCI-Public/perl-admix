# Copyright (c) 2000 - 2019 The Regents of the University of California.
# All rights reserved.	
# This includes the Generic yaml2rpm Makefile - most packaging should
# be able to use this.

include $(YAML2RPM_HOME)/sys/Makefile

SHELL = /bin/bash
PERLVER = $(shell $(GENERATE) --query=version perl.yaml)

# common and module specific filters
#FILTERSIN=$(shell ls filter*.in)
#FILTERS = $(FILTERSIN:.in=)

.PHONY: buildall

all: prep
	
#prep: $(FILTERS) MyConfig.pm
prep: MyConfig.pm

MyConfig.pm: MyConfig.pm.in
	sed 's%/root/%$(PWD)/%g' MyConfig.pm.in > MyConfig.pm

%.sh: %.sh.in
	sed 's/@VERSION@/$(PERLVER)/' $^ > $@

prepclean:
	-/bin/rm $(FILTERS) 
	-/bin/rm MyConfig.pm

cpandownload:
	for name in $(shell cat modules.bootstrap); do \
	    make download PKG=$$name; \
	done

AUTOYAML = $(shell cat buildorder)
cpandownload-desired:
	for name in $(AUTOYAML); do \
	    make download PKG=$$name; \
	done

desired-build: 
	echo $(AUTOYAML)
	( for mod in $(AUTOYAML); do					\
		make -e -f $(THISMAKE) $$mod.pkg;			\
		make -e -C $(LOCALREPODIR) createlocalrepo; 		\
		rpmname=$$($(GENERATE) --query=pkgname $$mod.yaml);	\
		yum -y -c $(LOCALREPODIR)/yum.conf install $$rpmname;	\
	  done								\
	)

DRPMS = $(subst auto,perl_$(PERLVER),$(AUTOYAML))
desired-rm:
	yum -y erase $(DRPMS)
	( for mod in $(DRPMS); do			\
	  	rm -rf ../RPMS/x86_64/$$mod-[0-9]* ;	\
	  done						\
	)

#temp:
#	( for mod in $(AUTOYAML); do			\
#		echo "  rpm: !include rpm.extras.yaml" >> $$mod.yaml; \
#	  done						\
#	)

addfilters:
	if [ -f add-filters.sh ]; then \
		/bin/bash add-filters.sh $(thismod) $(TMPBUILD) "$(GENERATE)"; \
	else \
		echo; \
	fi


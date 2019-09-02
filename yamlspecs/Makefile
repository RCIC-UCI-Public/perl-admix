# Copyright (c) 2000 - 2019 The Regents of the University of California.
# All rights reserved.	
# This includes the Generic yaml2rpm Makefile - most packaging should
# be able to use this.

include $(YAML2RPM_HOME)/sys/Makefile

SHELL = /bin/bash
PERLVER = $(shell $(GENERATE) --query=version perl.yaml)

FILTERS = \
filter-requires-perl.sh \
filter-requires-perlmodules.sh \
filter-requires-Module-Pluggable.sh \
filter-requires-ExtUtils-Helpers.sh \
filter-provides-perl.sh  \
filter-provides-perlmodules.sh \
filter-provides-Package-Stash.sh \
filter-provides-namespace-clean.sh

.PHONY: buildall

all: prep
	
prep: $(FILTERS) MyConfig.pm

MyConfig.pm: MyConfig.pm.in
	sed 's%/root/%$(PWD)/%g' MyConfig.pm.in > MyConfig.pm

%.sh: %.sh.in
	echo $(PERLVER)
	sed 's/@VERSION@/$(PERLVER)/' $^ > $@

prepclean:
	-/bin/rm $(FILTERS) 
	-/bin/rm MyConfig.pm

AUTOYAML = $(shell cat buildorder)

testbuild:
	for name in $(shell cat buildorder); do \
	    make download PKG=$$name; \
	done


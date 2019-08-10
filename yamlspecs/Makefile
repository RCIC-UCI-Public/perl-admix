# Copyright (c) 2000 - 2019 The Regents of the University of California.
# All rights reserved.	
# This includes the Generic yaml2rpm Makefile - most packaging should
# be able to use this.

include $(YAML2RPM_HOME)/sys/Makefile

SHELL = /bin/bash
PERLVER = $(shell $(GENERATE) --query=version perl.yaml)

FILTERS = filter-provides-perl.sh filter-requires-perl.sh \
          filter-provides-perlmodules.sh  filter-requires-perlmodules.sh

.PHONY: buildall

all: prep
	
prep: $(FILTERS) MyConfig.pm

MyConfig.pm: MyConfig.pm.in
	sed 's%/root/%$(PWD)/%g' MyConfig.pm.in > MyConfig.pm

%.sh: %.sh.in
	echo $(PERLVER)
	sed 's/@VERSION@/$(PERLVER)/' $^ > $@

clean:
	-/bin/rm $(FILTERS) 
	-/bin/rm MyConfig.pm

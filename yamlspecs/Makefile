# Copyright (c) 2000 - 2019 The Regents of the University of California.
# All rights reserved.	
# This includes the Generic yaml2rpm Makefile - most packaging should
# be able to use this.

include $(YAML2RPM_HOME)/sys/Makefile

MyConfig.pm: MyConfig.pm.in
	sed 's%/root/%$(PWD)/%g' MyConfig.pm.in > MyConfig.pm

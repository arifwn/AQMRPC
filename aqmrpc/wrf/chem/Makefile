# ============================================================================
# Name        : Makefile
# Author      : Arif Widi Nugroho
# Version     :
# Copyright   : 
# Description : Makefile for Hello World in Fortran
# ============================================================================

.PHONY: all clean

# Change this line if you are using a different Fortran compiler
FORTRAN_COMPILER = gfortran

all: src/WRFChemEmiss.f90
	$(FORTRAN_COMPILER) -O2 -ffree-form -fconvert=big-endian -o bin/WRFChemEmiss src/WRFChemEmiss.f90

clean:
	rm -f bin/WRFChemEmiss *.mod
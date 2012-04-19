! ============================================================================
! Name        : WRFChemEmiss.f90
! Author      : Arif Widi Nugroho
! Version     : 0.1
! Copyright   : 
! Description : Program ini membuat input data emisi untuk digunakan dalam
! 				pemodelan kualitas udara dengan menggunakan WRF/Chem
! ============================================================================

program WRFChemEmiss
    implicit none
!	IX2 = e_we - 1, JX2 = e_sn-1, kx = kemit
!	kemit: number of vertical level in emission file, 0 < kemit < e_vert
    INTEGER, PARAMETER :: NRADM=30, IX2=30, JX2=30, KX=1

    REAL, DIMENSION(IX2,KX,JX2,NRADM)   :: EM3RD
    REAL, DIMENSION(IX2,KX,JX2)         :: EM3RS
    CHARACTER(9), DIMENSION(NRADM)		:: ENAME
    INTEGER	:: IHR, N, I, J, K
    DATA ENAME /    &
     'e_so2 ','e_no  ','e_ald ','e_hcho','e_ora2',                     &
     'e_nh3 ','e_hc3 ','e_hc5 ','e_hc8 ',                              &
     'e_eth ','e_co  ','e_ol2 ','e_olt ','e_oli ','e_tol ','e_xyl ',   &
     'e_ket ','e_csl ','e_iso ','e_pm25i','e_pm25j',                   &
     'e_so4i','e_so4j','e_no3i','e_no3j','e_orgi','e_orgj','e_eci',    &
     'e_ecj','e_pm10'/


    print *, "WRFChem Emission Input Generator"

	print *, "Generating wrfem_00to12z_d01 ..."
    open(19,FILE='wrfem_00to12z_d01',FORM='UNFORMATTED')
    write(19)NRADM
    write(19)ENAME
	do IHR=1,12
		write(19)IHR
		do N=1,NRADM
!			EM3RS = 0
			do I=1,IX2
	        do K=1,KX
	        do J=1,JX2
				EM3RS(I,K,J) = 0
			end do
			end do
			end do
			if(N.EQ.1) then
! 	SO2 5625 mol/km2/jam
				EM3RS(15,1,15) = 9861.06/9.0
			end if
			WRITE(19)EM3RS
		end do
	end do
    close(19)
	print *, "... Done!"

	print *, "Generating wrfem_12to24z_d01 ..."
    open(19,FILE='wrfem_12to24z_d01',FORM='UNFORMATTED')
    write(19)NRADM
    write(19)ENAME
	do IHR=13,24
		write(19)IHR
		do N=1,NRADM
!			EM3RS = 0
			do I=1,IX2
	        do K=1,KX
	        do J=1,JX2
				EM3RS(I,K,J) = 0
			end do
			end do
			end do
			if(N.EQ.1) then
! 	SO2 5625 mol/km2/jam
				EM3RS(15,1,15) = 9861.06/9.0
			end if
			WRITE(19)EM3RS
		end do
	end do
    close(19)
	print *, "... Done!"
end program
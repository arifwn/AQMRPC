'reinit'
'open {{ ctl_file }}'

'set mpdset hires'
'set display color white'

'q file'
rec=sublin(result,5)
_endtime=subwrd(rec,12)

num_x=subwrd(rec,3)
num_y=subwrd(rec,6)
num_z=subwrd(rec,9)

say 't: ' _endtime
say 'x:' num_x
say 'y:' num_y
say 'z:' num_z


count = 1
while (count < _endtime)
  num = count
  'c'
  'set mpdset hires'
  'set t 'count

  'set gxout shaded'
  'set csmooth on'
  'd hgt'
  'cbarm'
  'set gxout contour'
  'd u;v'

  'draw title [T 'num%']'
  'printim {{ output_dir }}/t_'%num%'.png white'

  count = count + 1
endwhile

'quit'

; Tag 3  handler @ 0x1402A2830  (no Function record)
; Entry table slot @ 0x1404A5FA0

1402a2830:  CMP dword ptr [RDX + 0x4],0x0
1402a2834:  MOV R8D,dword ptr [RDX]
1402a2837:  JZ 0x1402a2841
1402a2839:  LEA RAX,[RDX + 0x8]
1402a283d:  MOV qword ptr [RCX + 0x68],RAX
1402a2841:  TEST R8D,R8D
1402a2844:  JZ 0x1402a284d
1402a2846:  MOV RAX,R8
1402a2849:  ADD RAX,qword ptr [RCX]
1402a284c:  RET

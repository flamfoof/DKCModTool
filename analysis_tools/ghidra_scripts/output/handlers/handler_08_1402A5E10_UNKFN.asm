; Tag 8  handler @ 0x1402A5E10  (no Function record)
; Entry table slot @ 0x1404A6018

1402a5e10:  MOVSXD RAX,dword ptr [RDX]
1402a5e13:  XOR R10D,R10D
1402a5e16:  MOV R9,qword ptr [0x1408a6c00]
1402a5e1d:  MOV R8,RAX
1402a5e20:  MOV RCX,qword ptr [0x1408a6c08]
1402a5e27:  MOV dword ptr [R9],EAX
1402a5e2a:  MOV EAX,dword ptr [RCX + RAX*0x4 + 0x64a0]
1402a5e31:  MOV qword ptr [R9 + 0xb0],R10
1402a5e38:  MOV qword ptr [R9 + 0xb8],R10
1402a5e3f:  MOV qword ptr [R9 + 0xc0],R10
1402a5e46:  MOV qword ptr [R9 + 0xc8],R10
1402a5e4d:  MOV dword ptr [R9 + 0x98],EAX
1402a5e54:  MOV qword ptr [R9 + 0xa8],R10
1402a5e5b:  MOV qword ptr [R9 + 0xa0],R10
1402a5e62:  MOV dword ptr [R9 + 0xd0],R10D
1402a5e69:  MOV qword ptr [R9 + 0xd8],R10
1402a5e70:  MOV RAX,qword ptr [RCX + R8*0x8 + 0x6470]
1402a5e78:  MOVUPS XMM0,xmmword ptr [RAX]
1402a5e7b:  MOVUPS xmmword ptr [R9 + 0xa0],XMM0
1402a5e83:  MOVUPS XMM1,xmmword ptr [RAX + 0x10]
1402a5e87:  MOVUPS xmmword ptr [R9 + 0xb0],XMM1
1402a5e8f:  MOVUPS XMM0,xmmword ptr [RAX + 0x20]
1402a5e93:  LEA RAX,[RDX + 0x4]
1402a5e97:  MOVUPS xmmword ptr [R9 + 0xc0],XMM0
1402a5e9f:  MOV qword ptr [R9 + 0xd8],R10
1402a5ea6:  RET

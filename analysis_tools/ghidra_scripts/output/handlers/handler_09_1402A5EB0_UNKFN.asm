; Tag 9  handler @ 0x1402A5EB0  (no Function record)
; Entry table slot @ 0x1404A6030

1402a5eb0:  MOV R9,qword ptr [0x1408a6c48]
1402a5eb7:  MOVZX R8D,word ptr [RDX]
1402a5ebb:  MOVSXD RAX,dword ptr [R9 + 0x18]
1402a5ebf:  IMUL RCX,RAX,0x64
1402a5ec3:  MOVZX EAX,word ptr [RDX + 0x2]
1402a5ec7:  LEA R8,[R8 + R8*0x2]
1402a5ecb:  ADD RCX,RAX
1402a5ece:  MOV RAX,qword ptr [0x1408a6c00]
1402a5ed5:  MOV RCX,qword ptr [R9 + RCX*0x8 + 0x50]
1402a5eda:  MOV qword ptr [RAX + R8*0x8 + 0x8],RCX
1402a5edf:  LEA RAX,[RDX + 0x4]
1402a5ee3:  RET

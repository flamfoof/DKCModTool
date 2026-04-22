; Tag 2  handler @ 0x1402A27E0  (no Function record)
; Entry table slot @ 0x1404A5F88

1402a27e0:  MOV EAX,dword ptr [RCX + 0x70]
1402a27e3:  TEST EAX,EAX
1402a27e5:  JLE 0x1402a280b
1402a27e7:  DEC EAX
1402a27e9:  MOV dword ptr [RCX + 0x70],EAX
1402a27ec:  TEST EAX,EAX
1402a27ee:  JLE 0x1402a27ff
1402a27f0:  MOV R8D,0x1
1402a27f6:  LEA RAX,[RDX + -0x4]
1402a27fa:  MOV dword ptr [RCX + 0xc],R8D
1402a27fe:  RET

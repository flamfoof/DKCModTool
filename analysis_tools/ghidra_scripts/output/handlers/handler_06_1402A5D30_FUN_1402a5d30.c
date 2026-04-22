// Tag 6  handler @ 0x1402A5D30  size=178
// Entry table slot @ 0x1404A5FE8


char * FUN_1402a5d30(longlong param_1,int *param_2)

{
  int *piVar1;
  int iVar2;
  int iVar3;
  longlong lVar4;
  longlong *plVar5;
  longlong lVar6;
  char local_28 [16];
  longlong lVar7;
  
  iVar2 = *param_2;
  piVar1 = param_2 + 1;
  lVar6 = -1;
  do {
    lVar7 = lVar6;
    lVar6 = lVar7 + 1;
  } while (*(char *)((longlong)piVar1 + lVar6) != '\0');
  iVar3 = *(int *)(param_1 + 0x48);
  lVar6 = param_1;
  lVar4 = FUN_1402b2f00(param_1,(char *)piVar1);
  if (iVar2 == 0xffff) {
    lVar4 = FUN_140098a20(lVar6,lVar4,iVar3);
  }
  else {
    lVar4 = FUN_14008c3e0(lVar6,iVar2,lVar4,iVar3);
  }
  *(longlong *)(param_1 + 0x10) = lVar4;
  if ((lVar4 != 0) && (lVar4 = *(longlong *)(lVar4 + 0x18), lVar4 != 0)) {
    local_28[0] = '\0';
    plVar5 = FUN_14002fe20(lVar6,(undefined8 *)piVar1,local_28);
    if (local_28[0] != '\0') {
      FUN_1402a5210(lVar4,plVar5);
    }
  }
  return (char *)((lVar7 + 5U & 0xfffffffffffffffc) + (longlong)piVar1);
}


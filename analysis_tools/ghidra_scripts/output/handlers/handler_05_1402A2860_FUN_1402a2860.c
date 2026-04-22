// Tag 5  handler @ 0x1402A2860  size=676
// Entry table slot @ 0x1404A5FD0


/* WARNING: Function: __security_check_cookie replaced with injection: security_check_cookie */
/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

uint * FUN_1402a2860(longlong *param_1,uint *param_2)

{
  char cVar1;
  uint uVar2;
  longlong *plVar3;
  longlong lVar4;
  undefined1 *puVar5;
  byte ****ppppbVar6;
  undefined8 ****ppppuVar7;
  char ****ppppcVar8;
  undefined8 *puVar9;
  byte ****ppppbVar10;
  ulonglong uVar11;
  ulonglong uVar12;
  ulonglong uVar13;
  undefined1 auStack_2b8 [32];
  char ***local_298 [2];
  ulonglong local_288;
  ulonglong uStack_280;
  undefined8 ***local_278 [2];
  ulonglong local_268;
  ulonglong uStack_260;
  byte ***local_258 [2];
  ulonglong local_248;
  ulonglong local_240;
  longlong local_238 [2];
  longlong local_228;
  undefined1 local_220 [232];
  char local_138 [46];
  undefined1 local_10a;
  ulonglong local_38;
  
  local_38 = DAT_1404f5810 ^ (ulonglong)auStack_2b8;
  uVar2 = *param_2;
  puVar9 = (undefined8 *)0x0;
  if (param_2[1] != 0) {
    puVar9 = (undefined8 *)((ulonglong)param_2[1] + *param_1);
  }
  if (uVar2 < 0x48) {
    local_248 = 0;
    local_240 = 0xf;
    local_258[0] = (byte ***)0x0;
    FUN_1403f9bd0((undefined1 (*) [16])local_238,0,0xf8);
    FUN_1400790d0(local_238);
    uVar12 = 0xffffffffffffffff;
    do {
      uVar12 = uVar12 + 1;
    } while (*(char *)((longlong)puVar9 + uVar12) != '\0');
    FUN_14002dcd0((longlong *)local_258,puVar9,uVar12);
    uVar12 = local_248;
    ppppbVar6 = local_258;
    if (0xf < local_240) {
      ppppbVar6 = (byte ****)local_258[0];
    }
    if (local_248 == 0) {
LAB_1402a297a:
      uVar11 = 0xffffffffffffffff;
    }
    else {
      FUN_1403f9bd0((undefined1 (*) [16])local_138,0,0x100);
      local_10a = 1;
      lVar4 = -1;
      if (uVar12 - 1 != -1) {
        lVar4 = uVar12 - 1;
      }
      ppppbVar10 = (byte ****)((longlong)ppppbVar6 + lVar4);
      cVar1 = local_138[*(byte *)ppppbVar10];
      while (cVar1 == '\0') {
        if (ppppbVar10 == ppppbVar6) goto LAB_1402a297a;
        ppppbVar10 = (byte ****)((longlong)ppppbVar10 + -1);
        cVar1 = local_138[*(byte *)ppppbVar10];
      }
      uVar11 = (longlong)ppppbVar10 - (longlong)ppppbVar6;
    }
    local_288 = _DAT_1404bda20;
    uStack_280 = _UNK_1404bda28;
    local_298[0] = (char ***)0x0;
    uVar13 = uVar11;
    if (uVar12 < uVar11) {
      uVar13 = uVar12;
    }
    ppppbVar6 = local_258;
    if (0xf < local_240) {
      ppppbVar6 = (byte ****)local_258[0];
    }
    FUN_14002dcd0((longlong *)local_298,ppppbVar6,uVar13);
    ppppcVar8 = local_298;
    if (0xf < uStack_280) {
      ppppcVar8 = (char ****)local_298[0];
    }
    plVar3 = FUN_14006adc0(&local_228,ppppcVar8,local_288);
    plVar3 = FUN_140069610(plVar3,0x1404ba790);
    local_268 = _DAT_1404bda20;
    uStack_260 = _UNK_1404bda28;
    local_278[0] = (undefined8 ****)0x0;
    if (local_248 < uVar11) {
                    /* WARNING: Subroutine does not return */
      FUN_14003b420();
    }
    uVar12 = 0xffffffffffffffff;
    if (local_248 - uVar11 != 0xffffffffffffffff) {
      uVar12 = local_248 - uVar11;
    }
    ppppbVar6 = local_258;
    if (0xf < local_240) {
      ppppbVar6 = (byte ****)local_258[0];
    }
    FUN_14002dcd0((longlong *)local_278,(undefined8 *)((longlong)ppppbVar6 + uVar11),uVar12);
    ppppuVar7 = local_278;
    if (0xf < uStack_260) {
      ppppuVar7 = (undefined8 ****)local_278[0];
    }
    FUN_14006adc0(plVar3,ppppuVar7,local_268);
    FUN_14002dc70((longlong *)local_278);
    FUN_14002dc70((longlong *)local_298);
    puVar5 = local_220;
    FUN_1400795f0((longlong)puVar5,(longlong *)local_298);
    ppppcVar8 = local_298;
    if (0xf < uStack_280) {
      ppppcVar8 = (char ****)local_298[0];
    }
    lVar4 = FUN_1402b2f00(puVar5,(char *)ppppcVar8);
    FUN_14002dc70((longlong *)local_298);
    *(longlong *)(DAT_1408a8b10 + 0x4b8 + (longlong)(int)uVar2 * 8) = lVar4;
    FUN_140078f20(local_238);
    FUN_14002dc70((longlong *)local_258);
  }
  return param_2 + 2;
}


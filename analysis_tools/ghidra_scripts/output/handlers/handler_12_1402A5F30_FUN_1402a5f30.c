// Tag 12  handler @ 0x1402A5F30  size=53
// Entry table slot @ 0x1404A6078


uint * FUN_1402a5f30(longlong param_1,uint *param_2)

{
  uint *puVar1;
  
  puVar1 = FUN_14008e190();
  *(uint **)(param_1 + 0x18) = puVar1;
  if (*param_2 < 5) {
    *(uint **)(param_1 + 0x20 + (longlong)(int)*param_2 * 8) = puVar1;
  }
  return param_2 + 1;
}


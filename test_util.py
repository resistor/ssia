def zeroAllInputs(dut):
    for i in dut.in_mem:
        yield i.eq(0)
    for i in dut.in_push:
        yield i.eq(0)
    for i in dut.in_stack_swizzle:
        for j in i:
            yield j.eq(0)
    for i in dut.in_writeback:
        yield i.eq(0)

def feedForwardSwizzles(dut):
    for stage in dut.in_stack_swizzle:
        for depth in range(len(stage)):
            yield stage[depth].eq(depth)
from top_stack import TopStack

def zeroAllInputs(dut: TopStack):
    for i in dut.in_mem:
        yield i.eq(0)
    for i in dut.in_push:
        yield i.eq(0)
    for i in dut.in_stack_swizzle:
        for j in i:
            yield j.eq(0)
    for i in dut.in_writeback:
        yield i.eq(0)

def feedForwardAtStage(dut: TopStack, stage: int):
    stack_depth = len(dut.in_stack_swizzle[stage])
    for slot in range(stack_depth):
        yield dut.in_stack_swizzle[stage][slot].eq(slot)

def feedForwardAllStages(dut: TopStack):
    for stage in range(len(dut.in_stack_swizzle)):
        yield from feedForwardAtStage(dut, stage)

def pushStackAtStage(dut: TopStack, stage: int):
    stack_depth = len(dut.in_stack_swizzle[stage])
    for slot in range(stack_depth):
        if slot == 0:
            yield dut.in_stack_swizzle[stage][slot].eq(stack_depth)
        else:
            yield dut.in_stack_swizzle[stage][slot].eq(slot-1)

def pushStackAllStages(dut: TopStack):
    for stage in range(len(dut.in_stack_swizzle)):
        yield from pushStackAtStage(dut, stage)

def popStackAtStage(dut: TopStack, stage: int):
    stack_depth = len(dut.in_stack_swizzle[stage])
    for slot in range(stack_depth):
        yield dut.in_stack_swizzle[stage][slot].eq(slot+1)

def popStackAllStages(dut: TopStack):
    for stage in range(len(dut.in_stack_swizzle)):
        yield from popStackAtStage(dut, stage)
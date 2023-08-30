from amaranth import *
from amaranth.hdl import *
from amaranth.back import verilog
from amaranth.lib.data import StructLayout
from top_stack import TopStack
from mid_stack import MidStack, MidStackCommand

class SSIA(Elaboratable):
    def __init__(self, register_width: int, top_stack_depth: int, mid_stack_depth: int, issue_stages: int, tag_width: int, writeback_count: int):
        self._top_stack_depth = top_stack_depth
        self._mid_stack_depth = mid_stack_depth
        self._tag_width = tag_width
        self._issue_stages = issue_stages
        self._register_width = register_width
        self._tag_width = tag_width
        self._writeback_count = writeback_count
        self._register_layout = StructLayout({
            "val": register_width,
            "tag": tag_width,
        })

        # in_push: one register+tag per issue stage to possibly be pushed onto the stack
        self.in_push = [Signal(self._register_layout, name="in_push_"+str(x)) for x in range(issue_stages)]

        # in_mem: one register+tag per issue stage that is pulled up from lower in the stack
        self.in_mem = [Signal(self._register_layout, name="in_mem_"+str(x)) for x in range(issue_stages)]

        # in_swizzle: one swizzle of the top-stack stack slots per stack slot per stage. Each swizzle
        # is log2_ceil(stack_depth) bits, except for the first and last one which are log2_ceil(stack_depth+1)
        # bits. Values 0 to stack_depth-1 encode the corresponding stack slot from the prior stage. Value
        # stack_depth is only value for the first and last swizzle, and encode selecting the values of
        # in_push and in_mem respectively.
        self.in_stack_swizzle = []
        for s in range(issue_stages):
            single_swizzle = []
            for d in range(top_stack_depth):
                if d == 0 or d == top_stack_depth-1:
                    single_swizzle.append(Signal(range(top_stack_depth+1), name="in_swizzle_"+str(s)+"_"+str(d)))
                else:
                    single_swizzle.append(Signal(range(top_stack_depth), name="in_swizzle_"+str(s)+"_"+str(d)))
            self.in_stack_swizzle.append(single_swizzle)

        # in_pushpop: One nop/pop/push command per stage.
        # 0b00 encodes no change, 0b10 encodes a pop, and 0b10 encodes a push.
        self.in_stack_pushpop = [Signal(MidStackCommand, name="in_pushpop_"+str(s)) for s in range(issue_stages)]

        # out_peek: two register+tag per issue stage that are the two top-most entries in the stack
        self.out_peek = [[Signal(self._register_layout, name = "out_peek_"+str(y)+"_"+str(x)) for x in range(2)] for y in range(issue_stages)]

        # out_bottom: one register+tag per issue stage that is the lowest entry in the stack
        self.out_bottom = [Signal(self._register_layout, name="out_bottom"+str(x)) for x in range(issue_stages)]

        # in_writeback: writeback_count register+tag which are tag-matched and written back each cycle
        self.in_writeback = [Signal(self._register_layout, name="in_cdb_"+str(x)) for x in range(writeback_count)]
    
    def elaborate(self, platform):
        m = Module()

        topStack = TopStack(register_width=self._register_width, stack_depth=self._top_stack_depth, issue_stages=self._issue_stages, tag_width=self._tag_width, writeback_count=self._writeback_count)
        m.submodules += topStack

        midStack = MidStack(register_width=self._register_width, stack_depth=self._mid_stack_depth, issue_stages=self._issue_stages, tag_width=self._tag_width, writeback_count=self._writeback_count)
        m.submodules += midStack

        for x in range(self._issue_stages):
            m.d.comb += topStack.in_push[x].eq(self.in_push[x])
            m.d.comb += topStack.in_mem[x].eq(midStack.out_peek[x])
            m.d.comb += midStack.in_push[x].eq(topStack.out_bottom[x])
            m.d.comb += midStack.in_mem[x].eq(self.in_mem[x])
            for y in range(self._top_stack_depth):
                m.d.comb += self.in_stack_swizzle[x][y].eq(topStack.in_stack_swizzle[x][y])
            m.d.comb += midStack.in_stack_pushpop[x].eq(self.in_stack_pushpop[x])

            for y in range(2):
                m.d.comb += self.out_peek[x][y].eq(topStack.out_peek[x][y])
            m.d.comb += self.out_bottom[x].eq(midStack.out_bottom[x])

        for x in range(self._writeback_count):
            m.d.comb += topStack.in_writeback[x].eq(self.in_writeback[x])
            m.d.comb += midStack.in_writeback[x].eq(self.in_writeback[x])

        return m
    
if __name__ == '__main__':
    ssia = SSIA(register_width=32, top_stack_depth=4, mid_stack_depth=4, issue_stages=4, tag_width=3, writeback_count=1)
    with open('ssia.v', 'w') as f:
        def asValue(v):
            return v.as_value()
        f.write(verilog.convert(ssia,
                                ports = [
                                         *map(asValue, ssia.in_push),
                                         *map(asValue, ssia.in_mem),
                                         *sum(ssia.in_stack_swizzle, []),
                                         *ssia.in_stack_pushpop,
                                         *map(asValue, sum(ssia.out_peek, [])),
                                         *map(asValue, ssia.out_bottom),
                                         *map(asValue, ssia.in_writeback),
                                        ]))
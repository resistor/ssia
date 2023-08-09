from amaranth import *
from amaranth.hdl import *
from amaranth.back import verilog
from amaranth.lib.enum import Enum
from amaranth.lib.data import StructLayout

class MidStackCommand(Enum):
    NOP = 0x0
    POP = 0x1
    PUSH = 0x2

# MidStack holds the generation of data on the processor stack immediately below the TopStack. Like TopStack it
# supports deferred writebacks, but unlike TopStack it only supports stack movement of the form NOP/POP/PUSH.
# Because of this, its area is linear with depth in contrast to TopStack. Stack regions below this no longer support
# deferred writebacks, so the processor will need to stall until writebacks can drain from this region as needed.
class MidStack(Elaboratable):
    def __init__(self, register_width: int, stack_depth: int, issue_stages: int, tag_width: int, writeback_count: int):
        self._stack_depth = stack_depth
        self._tag_width = tag_width
        self._issue_stages = issue_stages
        self._register_layout = StructLayout({
            "val": register_width,
            "tag": tag_width,
        })

        # in_push: one register+tag per issue stage to possibly be pushed onto the stack
        self.in_push = [Signal(self._register_layout, name="in_push_"+str(x)) for x in range(issue_stages)]

        # in_mem: one register+tag per issue stage that is pulled up from lower in the stack
        self.in_mem = [Signal(self._register_layout, name="in_mem_"+str(x)) for x in range(issue_stages)]

        # in_swizzle: One nop/pop/push command per stage.
        # 0b00 encodes no change, 0b10 encodes a pop, and 0b10 encodes a push.
        self.in_stack_swizzle = [Signal(MidStackCommand, name="in_swizzle_"+str(s)) for s in range(issue_stages)]

        # out_peek: one register+tag per issue stage that is the top-most entries in the stack
        self.out_peek = [Signal(self._register_layout, name = "out_peek_"+str(y)) for y in range(issue_stages)]

        # out_bottom: one register+tag per issue stage that is the lowest entry in the top-stack
        self.out_bottom = [Signal(self._register_layout, name="out_bottom"+str(x)) for x in range(issue_stages)]

        # in_writeback: writeback_count register+tag which are tag-matched and written back each cycle
        self.in_writeback = [Signal(self._register_layout, name="in_cdb_"+str(x)) for x in range(writeback_count)]

    def elaborate(self, platform):
        m = Module()

        # Stacks is a (S+1) x D grid of signals. The outer dimension is time, the inner dimension
        # is stack depth. Only the first stage (time = 0) is latched.
        stacks = [[Signal(self._register_layout, name="stack_"+str(y)+"_"+str(x)) for x in range(self._stack_depth)] for y in range(self._issue_stages+1)]

        for stage in range(self._issue_stages):
            # The top slot can be any feed-forward, one down, or a new pushed value.
            first_mux = Array([stacks[stage][0], stacks[stage][1], Cat(self.in_push[stage], Const(1, self._tag_width))])
            m.d.comb += stacks[stage+1][0].eq(first_mux[self.in_stack_swizzle[stage]])

            # Intermediary slots can be either feed-forward, one below, or one above.
            for d in range(self._stack_depth-2):
                mux = Array([stacks[stage][d+1], stacks[stage][d+2], stacks[stage][d]])
                m.d.comb += stacks[stage+1][d+1].eq(first_mux[self.in_stack_swizzle[stage]])

            # The bottom slot can be either feed-forward, a new value, or one about
            last_mux = Array([stacks[stage][d+1], self.in_mem[stage], stacks[stage][d]])
            m.d.comb += stacks[stage+1][self._stack_depth-1].eq(last_mux[self.in_stack_swizzle[stage]])

            # Expose the top stack entry at each stage as a "peek" value.
            m.d.comb += self.out_peek[stage].eq(stacks[stage][0])

            # Expose the bottom entry at each stage to the tidal stack.
            m.d.comb += self.out_bottom[stage].eq(stacks[stage][self._stack_depth-1])

        # Latch the final stage back to the concrete stack.
        for d in range(self._stack_depth):
            writeback_val = stacks[self._issue_stages][d]

            # Check for value write-backs before latching.
            for c in self.in_writeback:
                writeback_matched = (c['tag'] != 0) & (c['tag'] == stacks[self._issue_stages][d]['tag'])
                writeback_val = Mux(writeback_matched, Cat(c['val'], Const(1, self._tag_width)), writeback_val)
            m.d.sync += stacks[0][d].eq(writeback_val)

        return m
    
if __name__ == '__main__':
    mid_stack = MidStack(register_width=32, stack_depth=4, issue_stages=4, tag_width=3, writeback_count=1)
    with open('mid_stack.v', 'w') as f:
        def asValue(v):
            return v.as_value()
        f.write(verilog.convert(mid_stack,
                                ports = [
                                         *map(asValue, mid_stack.in_push),
                                         *map(asValue, mid_stack.in_mem),
                                         *mid_stack.in_stack_swizzle,
                                         *map(asValue, mid_stack.out_peek),
                                         *map(asValue, mid_stack.out_bottom),
                                         *map(asValue, mid_stack.in_writeback),
                                        ]))
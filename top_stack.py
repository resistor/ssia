from amaranth import *
from amaranth.hdl import *
from amaranth.back import verilog
from amaranth_boards.icestick import *
from amaranth.lib.enum import Enum
from amaranth.lib.data import StructLayout

class TopStack(Elaboratable):
    # register_width: the width in bits of individual stack entries
    # stack_depth: the number of stack entries stored within the top-stack region
    # issue_stages: the number of instructions to be issued in a single cycle
    # tag_width: the number of bits to use to tag unretired instructions
    # writeback_count: the number of values that can be retired in a single cycle
    def __init__(self, register_width, stack_depth, issue_stages, tag_width, writeback_count):
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

        # in_swizzle: one swizzle of the top-stack stack slots per stack slot per stage. Each swizzle
        # is log2_ceil(stack_depth) bits, except for the first and last one which are log2_ceil(stack_depth+1)
        # bits. Values 0 to stack_depth-1 encode the corresponding stack slot from the prior stage. Value
        # stack_depth is only value for the first and last swizzle, and encode selecting the values of
        # in_push and in_mem respectively.
        self.in_stack_swizzle = []
        for s in range(issue_stages):
            single_swizzle = []
            for d in range(stack_depth):
                if d == 0 or d == stack_depth-1:
                    single_swizzle.append(Signal(range(stack_depth+1), name="in_swizzle_"+str(s)+"_"+str(d)))
                else:
                    single_swizzle.append(Signal(range(stack_depth), name="in_swizzle_"+str(s)+"_"+str(d)))
            self.in_stack_swizzle.append(single_swizzle)

        # out_peek: two register+tag per issue stage that are the two top-most entries in the stack
        self.out_peek = [[Signal(self._register_layout, name = "out_peek_"+str(y)+"_"+str(x)) for x in range(2)] for y in range(issue_stages)]

        # out_bottom: one register+tag per issue stage that is the lowest entry in the top-stack
        self.out_bottom = [Signal(self._register_layout, name="out_bottom"+str(x)) for x in range(issue_stages)]

        # in_writeback: write_backcount register+tag which are tag-matched and written back each cycle
        self.in_writeback = [Signal(self._register_layout, name="in_cdb_"+str(x)) for x in range(writeback_count)]
    
    def elaborate(self, platform):
        m = Module()

        # Stacks is a (S+1) x D grid of signals. The outer dimension is time, the inner dimension
        # is stack depth. Only the first stage (time = 0) is latched.
        stacks = [[Signal(self._register_layout, name="stack_"+str(y)+"_"+str(x)) for x in range(self._stack_depth)] for y in range(self._issue_stages+1)]

        for stage in range(self._issue_stages):
            # The top slot can be any swizzle of the slots, or a pushed value.
            first_mux = Array([*stacks[stage], Cat(self.in_push[stage], Const(1, self._tag_width))])
            m.d.comb += stacks[stage+1][0].eq(first_mux[self.in_stack_swizzle[stage][0]])

            # Intermediary slots can be any swizzle of the slots.
            for d in range(self._stack_depth-2):
                mux = Array(stacks[stage])
                m.d.comb += stacks[stage+1][d+1].eq(first_mux[self.in_stack_swizzle[stage][d+1]])

            # The bottom slot can be any swizzle of the slots, or the top value from the tidal stack.
            last_mux = Array([*stacks[stage], self.in_mem[stage]])
            m.d.comb += stacks[stage+1][self._stack_depth-1].eq(last_mux[self.in_stack_swizzle[stage][self._stack_depth-1]])

            # Expose the top two stack entries at each stage as a "peek" values.
            for i in range(2):
                m.d.comb += self.out_peek[stage][i].eq(stacks[stage][i])
            
            # Expose the bottom entry at each stage to the tidal stack.
            m.d.comb += self.out_bottom[stage].eq(stacks[stage][self._stack_depth-1])
        
        # Latch the final stage back to the concrete stack.
        for d in range(self._stack_depth):
            writeback_val = stacks[self._issue_stages][d]

            # Check for value write-backs before latching.
            for c in self.in_writeback:
                writeback_matched = (c['tag'] != 0) & (c['tag'] == stacks[self._stack_depth][d]['tag'])
                writeback_val = Mux(writeback_matched, Cat(c['val'], Const(1, self._tag_width)), writeback_val)
            m.d.sync += stacks[0][d].eq(writeback_val)

        return m

if __name__ == '__main__':
    top_stack = TopStack(register_width=32, stack_depth=4, issue_stages=4, tag_width=3, writeback_count=1)
    with open('top_stack.v', 'w') as f:
        def asValue(v):
            return v.as_value()
        f.write(verilog.convert(top_stack,
                                ports = [
                                         *map(asValue, top_stack.in_push),
                                         *map(asValue, top_stack.in_mem),
                                         *sum(top_stack.in_stack_swizzle, []),
                                         *map(asValue, sum(top_stack.out_peek, [])),
                                         *map(asValue, top_stack.out_bottom),
                                         *map(asValue, top_stack.in_writeback),
                                        ]))
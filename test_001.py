from amaranth.sim import Simulator
from top_stack import TopStack
from test_util import *

dut = TopStack(register_width=32, stack_depth=4, issue_stages=4, tag_width=3, writeback_count=1)

# Test 001: All zero inputs.
def test_process():
    yield from zeroAllInputs(dut)
    yield
    for stage in dut.out_peek:
        for peek in stage:
            assert (yield peek['tag']) == 0
            assert (yield peek['val']) == 0
    for bottom in dut.out_bottom:
        assert (yield bottom['tag']) == 0
        assert (yield bottom['val']) == 0

def test():
    sim = Simulator(dut)
    sim.add_clock(1e-6)
    sim.add_sync_process(test_process)
    with sim.write_vcd('test_001.vcd'):
        sim.run()

if __name__ == '__main__':
    test()
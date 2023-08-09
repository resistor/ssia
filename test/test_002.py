from amaranth.sim import Simulator
from ssia.top_stack import TopStack
from util import *

dut = TopStack(register_width=32, stack_depth=4, issue_stages=4, tag_width=3, writeback_count=1)

# Test 002: Set top slot in stage 1, simple feed-forward
def process():
    yield from zeroAllInputs(dut)
    yield from feedForwardAllStages(dut)
    yield dut.in_push[0].eq(0x7FFFFFFFF)
    yield dut.in_stack_swizzle[0][0].eq(4)

    # On cycle 0, the value should be in the
    # top stack slot for all issue stages.
    yield
    assert (yield dut.out_peek[0][0]['tag']) == 0
    assert (yield dut.out_peek[0][0]['val']) == 0
    assert (yield dut.out_peek[0][1]['tag']) == 0
    assert (yield dut.out_peek[0][1]['val']) == 0
    assert (yield dut.out_peek[1][0]['tag']) == 7
    assert (yield dut.out_peek[1][0]['val']) == 0xFFFFFFFF
    assert (yield dut.out_peek[1][1]['tag']) == 0
    assert (yield dut.out_peek[1][1]['val']) == 0
    assert (yield dut.out_peek[2][0]['tag']) == 7
    assert (yield dut.out_peek[2][0]['val']) == 0xFFFFFFFF
    assert (yield dut.out_peek[2][1]['tag']) == 0
    assert (yield dut.out_peek[2][1]['val']) == 0
    assert (yield dut.out_peek[3][0]['tag']) == 7
    assert (yield dut.out_peek[3][0]['val']) == 0xFFFFFFFF
    assert (yield dut.out_peek[3][1]['tag']) == 0
    assert (yield dut.out_peek[3][1]['val']) == 0
    assert (yield dut.out_bottom[0]['tag']) == 0
    assert (yield dut.out_bottom[0]['val']) == 0
    assert (yield dut.out_bottom[1]['tag']) == 0
    assert (yield dut.out_bottom[1]['val']) == 0
    assert (yield dut.out_bottom[2]['tag']) == 0
    assert (yield dut.out_bottom[2]['val']) == 0
    assert (yield dut.out_bottom[3]['tag']) == 0
    assert (yield dut.out_bottom[3]['val']) == 0

    # After subsequent cycles, the value should be in the top
    # slot for all stages.
    for i in range(3):
        yield
        assert (yield dut.out_peek[0][0]['tag']) == 7
        assert (yield dut.out_peek[0][0]['val']) == 0xFFFFFFFF
        assert (yield dut.out_peek[0][1]['tag']) == 0
        assert (yield dut.out_peek[0][1]['val']) == 0
        assert (yield dut.out_peek[1][0]['tag']) == 7
        assert (yield dut.out_peek[1][0]['val']) == 0xFFFFFFFF
        assert (yield dut.out_peek[1][1]['tag']) == 0
        assert (yield dut.out_peek[1][1]['val']) == 0
        assert (yield dut.out_peek[2][0]['tag']) == 7
        assert (yield dut.out_peek[2][0]['val']) == 0xFFFFFFFF
        assert (yield dut.out_peek[2][1]['tag']) == 0
        assert (yield dut.out_peek[2][1]['val']) == 0
        assert (yield dut.out_peek[3][0]['tag']) == 7
        assert (yield dut.out_peek[3][0]['val']) == 0xFFFFFFFF
        assert (yield dut.out_peek[3][1]['tag']) == 0
        assert (yield dut.out_peek[3][1]['val']) == 0
        assert (yield dut.out_bottom[0]['tag']) == 0
        assert (yield dut.out_bottom[0]['val']) == 0
        assert (yield dut.out_bottom[1]['tag']) == 0
        assert (yield dut.out_bottom[1]['val']) == 0
        assert (yield dut.out_bottom[2]['tag']) == 0
        assert (yield dut.out_bottom[2]['val']) == 0
        assert (yield dut.out_bottom[3]['tag']) == 0
        assert (yield dut.out_bottom[3]['val']) == 0

def test(debug: bool = False):
    sim = Simulator(dut)
    sim.add_clock(1e-6)
    sim.add_sync_process(process)
    if debug:
        with sim.write_vcd('test_002.vcd'):
            sim.run()
    else:
        sim.run()

if __name__ == '__main__':
    test(debug = True)
from amaranth.sim import Simulator
from ssia.top_stack import TopStack

dut = TopStack(register_width=32, stack_depth=4, issue_stages=4, tag_width=3, writeback_count=1)

# Test 003: Push the four values in a single cycle
def process():
    yield from dut.zeroAllInputs()
    yield from dut.pushStackAllStages()
    yield dut.in_push[0].eq(0x112345678)
    yield dut.in_push[1].eq(0x287654321)
    yield dut.in_push[2].eq(0x39ABCDEF0)
    yield dut.in_push[3].eq(0x40FEDCBA9)

    # On cycle 0, the values move down through the stack
    # gradually replacing the initial zeros.
    yield
    assert (yield dut.out_peek[0][0]['tag']) == 0
    assert (yield dut.out_peek[0][0]['val']) == 0
    assert (yield dut.out_peek[0][1]['tag']) == 0
    assert (yield dut.out_peek[0][1]['val']) == 0
    assert (yield dut.out_peek[1][0]['tag']) == 0x1
    assert (yield dut.out_peek[1][0]['val']) == 0x12345678
    assert (yield dut.out_peek[1][1]['tag']) == 0
    assert (yield dut.out_peek[1][1]['val']) == 0
    assert (yield dut.out_peek[2][0]['tag']) == 0x2
    assert (yield dut.out_peek[2][0]['val']) == 0x87654321
    assert (yield dut.out_peek[2][1]['tag']) == 0x1
    assert (yield dut.out_peek[2][1]['val']) == 0x12345678
    assert (yield dut.out_peek[3][0]['tag']) == 0x3
    assert (yield dut.out_peek[3][0]['val']) == 0x9ABCDEF0
    assert (yield dut.out_peek[3][1]['tag']) == 0x2
    assert (yield dut.out_peek[3][1]['val']) == 0x87654321
    assert (yield dut.out_bottom[0]['tag']) == 0
    assert (yield dut.out_bottom[0]['val']) == 0
    assert (yield dut.out_bottom[1]['tag']) == 0
    assert (yield dut.out_bottom[1]['val']) == 0
    assert (yield dut.out_bottom[2]['tag']) == 0
    assert (yield dut.out_bottom[2]['val']) == 0
    assert (yield dut.out_bottom[3]['tag']) == 0
    assert (yield dut.out_bottom[3]['val']) == 0

    # On subsequent cycles, the same values are pushed
    # again in the same sequence, pushing down the values
    # that were already present
    for i in range(3):
        yield
        assert (yield dut.out_peek[0][0]['tag']) == 0x4
        assert (yield dut.out_peek[0][0]['val']) == 0x0FEDCBA9
        assert (yield dut.out_peek[0][1]['tag']) == 0x3
        assert (yield dut.out_peek[0][1]['val']) == 0x9ABCDEF0
        assert (yield dut.out_peek[1][0]['tag']) == 0x1
        assert (yield dut.out_peek[1][0]['val']) == 0x12345678
        assert (yield dut.out_peek[1][1]['tag']) == 0x4
        assert (yield dut.out_peek[1][1]['val']) == 0x0FEDCBA9
        assert (yield dut.out_peek[2][0]['tag']) == 0x2
        assert (yield dut.out_peek[2][0]['val']) == 0x87654321
        assert (yield dut.out_peek[2][1]['tag']) == 0x1
        assert (yield dut.out_peek[2][1]['val']) == 0x12345678
        assert (yield dut.out_peek[3][0]['tag']) == 0x3
        assert (yield dut.out_peek[3][0]['val']) == 0x9ABCDEF0
        assert (yield dut.out_peek[3][1]['tag']) == 0x2
        assert (yield dut.out_peek[3][1]['val']) == 0x87654321
        assert (yield dut.out_bottom[0]['tag']) == 0x1
        assert (yield dut.out_bottom[0]['val']) == 0x12345678
        assert (yield dut.out_bottom[1]['tag']) == 0x2
        assert (yield dut.out_bottom[1]['val']) == 0x87654321
        assert (yield dut.out_bottom[2]['tag']) == 0x3
        assert (yield dut.out_bottom[2]['val']) == 0x9ABCDEF0
        assert (yield dut.out_bottom[3]['tag']) == 0x4
        assert (yield dut.out_bottom[3]['val']) == 0x0FEDCBA9

def test(debug: bool = False):
    sim = Simulator(dut)
    sim.add_clock(1e-6)
    sim.add_sync_process(process)
    if debug:
        with sim.write_vcd('test_003.vcd'):
            sim.run()
    else:
        sim.run()

if __name__ == '__main__':
    test(debug = True)
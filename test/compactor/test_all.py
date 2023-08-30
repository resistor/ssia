from amaranth.sim import Simulator, Settle
from ssia.compactor import Compactor

dut = Compactor(width=32, count=4)

def process():
    yield from dut.zeroAllInputs()
    yield Settle()
    assert (yield dut.output_val) == 0
    assert (yield dut.output_count) == 0

    for i in range(dut._count):
        yield from dut.zeroAllInputs()
        yield dut.input_en[i].eq(1)
        yield dut.input[i].eq(0xFFFFFFFF)
        yield Settle()
        assert (yield dut.output_count) == 1
        assert (yield dut.output_val) == 0xFFFFFFFF

    for i in range(dut._count):
        for j in range(dut._count):
            if i == j:
                continue
            yield from dut.zeroAllInputs()
            yield dut.input_en[i].eq(1)
            yield dut.input_en[j].eq(1)
            yield dut.input[i].eq(0xFFFFFFFF)
            yield dut.input[j].eq(0xEEEEEEEE)
            yield Settle()
            assert (yield dut.output_count) == 2
            if i < j:
                assert (yield dut.output_val) == 0xEEEEEEEEFFFFFFFF
            else:
                assert (yield dut.output_val) == 0xFFFFFFFFEEEEEEEE

    for i in range(dut._count):
        for j in range(dut._count):
            for k in range(dut._count):
                if i == j:
                    continue
                if i == k:
                    continue
                if j == k:
                    continue
                yield from dut.zeroAllInputs()
                yield dut.input_en[i].eq(1)
                yield dut.input_en[j].eq(1)
                yield dut.input_en[k].eq(1)
                yield dut.input[i].eq(0xFFFFFFFF)
                yield dut.input[j].eq(0xEEEEEEEE)
                yield dut.input[k].eq(0xDDDDDDDD)
                yield Settle()
                assert (yield dut.output_count) == 3
                if i < j < k:
                    assert (yield dut.output_val) == 0xDDDDDDDDEEEEEEEEFFFFFFFF
                elif j < i < k:
                    assert (yield dut.output_val) == 0xDDDDDDDDFFFFFFFFEEEEEEEE
                elif i < k < j:
                    assert (yield dut.output_val) == 0xEEEEEEEEDDDDDDDDFFFFFFFF
                elif j < k < i:
                    assert (yield dut.output_val) == 0xFFFFFFFFDDDDDDDDEEEEEEEE
                elif k < i < j:
                    assert (yield dut.output_val) == 0xEEEEEEEEFFFFFFFFDDDDDDDD
                else:
                    assert (yield dut.output_val) == 0xFFFFFFFFEEEEEEEEDDDDDDDD

    yield from dut.zeroAllInputs()
    yield dut.input_en[0].eq(1)
    yield dut.input_en[1].eq(1)
    yield dut.input_en[2].eq(1)
    yield dut.input_en[3].eq(1)
    yield dut.input[0].eq(0xFFFFFFFF)
    yield dut.input[1].eq(0xEEEEEEEE)
    yield dut.input[2].eq(0xDDDDDDDD)
    yield dut.input[3].eq(0xCCCCCCCC)
    yield Settle()
    assert (yield dut.output_count) == 4
    assert (yield dut.output_val) == 0xCCCCCCCCDDDDDDDDEEEEEEEEFFFFFFFF

def test(debug: bool = False):
    sim = Simulator(dut)
    sim.add_process(process)
    if debug:
        with sim.write_vcd('test_all_zero.vcd'):
            sim.run()
    else:
        sim.run()

if __name__ == '__main__':
    test(debug = True)
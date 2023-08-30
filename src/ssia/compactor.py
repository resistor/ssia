from amaranth import *
from amaranth.hdl import *
from amaranth.back import verilog
from amaranth.lib.coding import PriorityEncoder

class Compactor(Elaboratable):
    def __init__(self, width: int, count: int):
        self._width = width
        self._count = count
        self.input = [Signal(width, name="input_"+str(x)) for x in range(count)]
        self.input_en = [Signal(1, name="input_en_"+str(x)) for x in range(count)]
        self.output_val = Signal(count*width, name="output_val")
        self.output_count = Signal(range(count+1), name="output_count")
        self.initial_concat = Signal(count*width)

    def elaborate(self, platform):
        m = Module()
        self.priority_encoders = [PriorityEncoder(self._count) for x in range(self._count)]
        m.submodules += self.priority_encoders

        self.concat_en = [Signal(self._count, name = "concat_en_"+str(x)) for x in range(self._count)]
        self.parts = [Signal(self._width, name="part_"+str(x)) for x in range(self._count)]

        array = Array(self.input)
        array.append(0)
        for i in range(self._count):
            if i == 0:
                m.d.comb += self.concat_en[0].eq(Cat(*self.input_en))
            else:
                m.d.comb += self.concat_en[i].eq(self.concat_en[i-1] & (self.concat_en[i-1]-1))
            m.d.comb += self.priority_encoders[i].i.eq(self.concat_en[i])
            m.d.comb += self.parts[i].eq(array[Cat(self.priority_encoders[i].o, self.priority_encoders[i].n)])
        m.d.comb += self.output_val.eq(Cat(*self.parts))
        m.d.comb += self.output_count.eq(sum(self.input_en))
        return m
    
    # Testing helpers
    def zeroAllInputs(self):
        for i in self.input:
            yield i.eq(0)
        for i in self.input_en:
            yield i.eq(0)
    
if __name__ == '__main__':
    compactor = Compactor(width=32, count=4)
    with open('compactor.v', 'w') as f:
        f.write(verilog.convert(compactor,
                                ports = [
                                         *compactor.input,
                                         *compactor.input_en,
                                         compactor.output_val,
                                         compactor.output_count,
                                        ]))
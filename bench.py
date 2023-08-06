from amaranth.sim import Simulator
from top_stack import TopStack
import test_001
import test_002
import test_003
import test_004
import test_005

tests = [
    test_001,
    test_002,
    test_003,
    test_004,
    test_005,
]
for i in range(len(tests)):
    print('TEST {:0>3} ... '.format(i+1), end='')
    tests[i].test()
    print('PASSED')

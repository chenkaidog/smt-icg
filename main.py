from domain.parser import PDDLParser
from generator import Generator
from z3 import simplify
import time
import os


if __name__ == '__main__':
    start = time.time()
    domain = PDDLParser("./pddl/Empty_and_divide.pddl")
    # domain = PDDLParser("./pddl/two_piled_nim.pddl")
    # domain = PDDLParser("./pddl/Chomp_game.pddl")
    gen = Generator(domain)
    formula_template = gen.generate_formula(5)
    formula = simplify(formula_template.formula_model())
    cost1 = time.time() - start
    print('*'*50)
    print('N-formula:\n\t %s' % formula)

    strategies = gen.generate_strategy()
    cost2 = time.time() - start
    print('*' * 50)
    print(strategies)

    if not os.path.exists("./log"):
        os.mkdir("./log")
    with open("./log/%s" % domain.name, "a") as f:
        print("\n*******************Finished*******************")
        print('N-formula:\n\t %s' % formula)
        print('time cost:\n\t %s' % cost1)
        print('strategies:\n\t %s' % strategies)
        print('time cost:\n\t %s' % cost2)

        print('\nN-formula:\t %s' % formula, file=f)
        print('time cost:\t %s' % cost1, file=f)
        print('strategies:\t %s' % strategies, file=f)
        print('time cost:\t %s' % cost2, file=f)
        print()

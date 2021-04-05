from z3 import *


def combine(iter):
    tmp_list = [i for i in iter]
    res = tmp_list[0]
    for i in tmp_list[1:]:
        res += i
    return res


def co_prime(num1, num2):
    for num in range(2, min(num1, num2) + 1):
        if num1 % num == 0 and num2 % num == 0:
            return False
    return True


def gcd(*nums):
    min_num = 1 << 32
    for num in nums:
        if num != 0:
            min_num = min(min_num, abs(num))
    for i in range(min_num, 1, -1):
        flag = True
        for num in nums:
            if num % i != 0:
                flag = False
                break
        if flag:
            return i
    return 1


class FormulaTemplate:
    def __init__(self, vi, k, h, m, timeout=3000000):
        self.k = k  # amount of clause
        self.h = h  # number of inequality
        self.m = m  # number of mode number
        self.vi = vi
        n = len(vi)
        self.n = n
        self.aeij = [[Int('ae' + str(i) + str(j)) for j in range(n)] for i in range(h)]
        self.bi = [Int('b' + str(i)) for i in range(h)]
        self.amij = [[Int('am' + str(i) + str(j)) for j in range(n)] for i in range(m)]
        self.ei = [Int('e' + str(i)) for i in range(m)]
        self.ci = [Int('c' + str(i)) for i in range(m)]
        self.heij = [[Bool('h_e' + str(j) + str(i)) for i in range(h)] for j in range(k)]
        self.hgeij = [[Bool('h_ge' + str(j) + str(i)) for i in range(h)] for j in range(k)]
        self.hleij = [[Bool('h_le' + str(j) + str(i)) for i in range(h)] for j in range(k)]
        self.tij = [[Bool('t' + str(j) + str(i)) for i in range(m)] for j in range(k)]
        self.ntij = [[Bool('nt' + str(j) + str(i)) for i in range(m)] for j in range(k)]
        self.s = Solver()
        for i in range(h):
            # 不等式系数ae_ij不能全部为0
            self.s.add(Or(*[a > 0 for a in self.aeij[i]]))
            for j in range(i + 1, h):
                self.s.add(Or(*[self.aeij[i][w] != self.aeij[j][w] for w in range(n)]))
        for i in range(m):
            # 模等式的系数am_ij不能全部小于等于0
            self.s.add(Or(*[am > 0 for am in self.amij[i]]))
            # 模等式的系数am_ij不能大于模e
            self.s.add(*[And(0 <= am, am < self.ei[i]) for am in self.amij[i]])
            for j in range(i + 1, m):
                self.s.add(Or(*[self.amij[i][w] != self.amij[j][w] for w in range(m)]))
        # 余数c_i必须小于模e
        self.s.add(*[And(self.ei[i] > self.ci[i], self.ci[i] >= 0) for i in range(m)])
        # 模必须大于等于2，并且小于一定范围
        self.s.add(*[And(e <= 2 * m, e >= 2) for e in self.ei])
        for i in range(k):
            # 判断条件一定有一个是False，避免逻辑出现False
            # self.s.add(*[Not(And(self.heij[i][j], self.hgeij[i][j], self.hleij[i][j])) for j in range(h)])
            # self.s.add(*[Not(And(self.tij[i][j], self.ntij[i][j])) for j in range(m)])
            for j in range(i + 1, k):
                all_true = [And(self.heij[i][w], self.hgeij[i][w], self.hleij[i][w]) for w in range(h)]
                all_true.extend([And(self.tij[i][w], self.ntij[i][w]) for w in range(m)])
                struct_const = [Or(self.heij[i][w] != self.heij[j][w],
                                   self.hgeij[i][w] != self.hgeij[j][w],
                                   self.hleij[i][w] != self.hleij[j][w]) for w in range(h)]
                struct_const.extend([Or(self.tij[i][w] != self.tij[j][w],
                                        self.ntij[i][w] != self.ntij[j][w]) for w in range(m)])

                self.s.add(Or(*struct_const, *all_true))

        self.s.set("timeout", timeout)

    def add(self, example, label):
        self.s.add(self.encoding(example, label))

    def check(self):
        check = self.s.check()
        if check == sat:
            self.solve_model()
        return check

    def encoding(self, example, label):
        Equ = [combine(example[j] * self.aeij[i][j] for j in range(self.n)) != self.bi[i] for i in range(self.h)]
        Ge = [combine(example[j] * self.aeij[i][j] for j in range(self.n)) >= self.bi[i] for i in range(self.h)]
        Le = [combine(example[j] * self.aeij[i][j] for j in range(self.n)) <= self.bi[i] for i in range(self.h)]
        Me = [combine(example[j] * self.amij[i][j] for j in range(self.n)) % self.ei[i] == self.ci[i] for i in
              range(self.m)]
        Tk = []
        for k in range(self.k):
            clause = []
            clause.extend([Implies(self.heij[k][h], Equ[h]) for h in range(self.h)])
            clause.extend([Implies(self.hgeij[k][h], Ge[h]) for h in range(self.h)])
            clause.extend([Implies(self.hleij[k][h], Le[h]) for h in range(self.h)])
            clause.extend([Implies(self.tij[k][m], Me[m]) for m in range(self.m)])
            clause.extend([Implies(self.ntij[k][m], Not(Me[m])) for m in range(self.m)])
            Tk.append(And(*clause))
        return Or(*Tk) == label

    def solve_model(self):
        model = self.s.model()
        self.M = [[model[self.amij[i][j]].as_long() if model[self.amij[i][j]] is not None else 0
                   for j in range(self.n)]
                  for i in range(self.m)]
        self.E = [model[self.ei[i]].as_long() if model[self.ei[i]] is not None else 1 for i in range(self.m)]
        self.C = [model[self.ci[i]].as_long() if model[self.ci[i]] is not None else 0 for i in range(self.m)]
        self.A = [[model[self.aeij[i][j]].as_long() if model[self.aeij[i][j]] is not None else 0
                   for j in range(self.n)]
                  for i in range(self.h)]
        self.B = [model[self.bi[i]].as_long() if model[self.bi[i]] is not None else 0 for i in range(self.h)]
        self.He = [
            [bool(model[self.heij[i][j]]) if model[self.heij[i][j]] is not None else False
             for j in range(self.h)]
            for i in range(self.k)
        ]
        self.Hge = [
            [bool(model[self.hgeij[i][j]]) if model[self.hgeij[i][j]] is not None else False
             for j in range(self.h)]
            for i in range(self.k)
        ]
        self.Hle = [
            [bool(model[self.hleij[i][j]]) if model[self.hleij[i][j]] is not None else False
             for j in range(self.h)]
            for i in range(self.k)
        ]
        self.T = [
            [bool(model[self.tij[i][j]]) if model[self.tij[i][j]] is not None else False
             for j in range(self.m)]
            for i in range(self.k)
        ]
        self.Nt = [
            [bool(model[self.ntij[i][j]]) if model[self.ntij[i][j]] is not None else False
             for j in range(self.m)]
            for i in range(self.k)
        ]
        for i in range(self.m):
            flag = True
            pix = -1
            for am in self.M[i]:
                if pix == -1:
                    if am != 0:
                        pix = am
                elif am != 0 and am != pix:
                    flag = False
                    break
            if flag:
                if self.C[i] == 0:
                    if co_prime(pix, self.E[i]):
                        for j in range(self.n):
                            if self.M[i][j] != 0:
                                self.M[i][j] = 1
                    else:
                        div = gcd(pix, self.E[i])
                        self.E[i] /= div
                        for j in range(self.n):
                            self.M[i][j] /= div
                else:
                    div = gcd(pix, self.E[i], self.C[i])
                    self.E[i] /= div
                    self.C[i] /= div
                    for j in range(self.n):
                        self.M[i][j] /= div
        for i in range(self.h):
            divisior = gcd(*self.A[i], self.B[i])
            self.B[i] /= divisior
            for j in range(self.n):
                self.A[i][j] /= divisior

    def formula_model(self, *val):
        if len(val) == 0:
            val = self.vi
        formu = []
        for k in range(self.k):
            clause = []
            for h in range(self.h):
                Coe = combine(self.A[h][j] * val[j] for j in range(self.n))
                status = (self.He[k][h], self.Hge[k][h], self.Hle[k][h])
                if status == (False, False, True):
                    clause.append(Coe <= self.B[h])
                elif status == (False, True, False):
                    clause.append(Coe >= self.B[h])
                elif status == (True, False, False):
                    clause.append(Coe != self.B[h])
                elif status == (False, True, True):
                    clause.append(Coe == self.B[h])
                elif status == (True, False, True):
                    clause.append(Coe < self.B[h])
                elif status == (True, True, False):
                    clause.append(Coe > self.B[h])
                elif status == (True, True, True):
                    clause.append(False)
            for m in range(self.m):
                status = (self.T[k][m], self.Nt[k][m])
                if status == (True, False):
                    clause.append(combine(self.M[m][j] * val[j] for j in range(self.n)) % self.E[m] == self.C[m])
                elif status == (False, True):
                    clause.append(combine(self.M[m][j] * val[j] for j in range(self.n)) % self.E[m] != self.C[m])
                elif status == (True, True):
                    clause.append(False)
            formu.append(And(*clause))
        return simplify(Or(*formu))

    def refine_model(self):
        formu_arr = []
        for k in range(self.k):
            clause = []
            for h in range(self.h):
                Coe = combine(self.A[h][j] * self.vi[j] for j in range(self.n))
                status = (self.He[k][h], self.Hge[k][h], self.Hle[k][h])
                if status == (False, False, True):
                    clause.append([Coe < self.B[h], Coe == self.B[h]])
                elif status == (False, True, False):
                    clause.append([Coe > self.B[h], Coe == self.B[h]])
                elif status == (True, False, False):
                    clause.append([Coe < self.B[h], Coe > self.B[h]])
                elif status == (False, True, True):
                    clause.append([Coe == self.B[h]])
                elif status == (True, False, True):
                    clause.append([Coe < self.B[h]])
                elif status == (True, True, False):
                    clause.append([Coe > self.B[h]])
                elif status == (True, True, True):
                    clause.append([False])
            for m in range(self.m):
                status = (self.T[k][m], self.Nt[k][m])
                Com = combine(self.M[m][j] * self.vi[j] for j in range(self.n))
                if status == (True, False):
                    clause.append([Com % self.E[m] == self.C[m]])
                elif status == (False, True):
                    mod_clause = []
                    for i in range(int(self.E[m])):
                        if i != self.C[m]:
                            mod_clause.append(Com % self.E[m] == i)
                    clause.append(mod_clause)
                elif status == (True, True):
                    clause.append([False])
            formu_arr.append(clause)
        return formu_arr


class EquTemplate:
    def __init__(self, n):
        self.vi = [Int('v' + str(i)) for i in range(n)]
        self.b = Int('b')
        self.s = Solver()

    def add(self, vector):
        vi, target = vector[:-1], vector[-1]
        expr = combine(vi[i] * self.vi[i] for i in range(len(self.vi))) + self.b == target
        self.s.add(expr)

    def check(self):
        return self.s.check()

    def solve_model(self):
        model = self.s.model()
        V = [model[v].as_long() if model[v] is not None else 0 for v in self.vi]
        B = model[self.b].as_long() if model[self.b] is not None else 0
        expr = combine(V[i] * self.vi[i] for i in range(len(self.vi))) + B
        return simplify(expr)


if __name__ == '__main__':
    # smt = FormulaTemplate([Int('v1'), Int('v2')], 4, 3, 2)
    # smt.add([1, 2], True)
    # smt.add([2, 3], False)
    # print(smt.s)
    # print(smt.check())
    #
    # arr = smt.refine_model()
    # for a in arr:
    #     print(a)
    #
    # formu = smt.formula_model()
    # print(formu)
    # print('-' * 50)
    # print(simplify(formu))
    # print('-' * 50)

    smt = EquTemplate(2)
    smt.add([1, 2, 6])
    smt.add([2, 1, 5])
    smt.add([2, 2, 7])
    if smt.check() == sat:
        print(smt.solve_model()) # 1*v0 + 2*v1 + 1
    else:
        print(unsat)

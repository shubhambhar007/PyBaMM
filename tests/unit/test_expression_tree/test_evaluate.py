#
# Test for the evaluate functions
#
import pybamm

from tests import get_mesh_for_testing, get_discretisation_for_testing
import unittest
import numpy as np
import scipy.sparse
import os
from collections import OrderedDict


class TestEvaluate(unittest.TestCase):
    def test_find_symbols(self):
        a = pybamm.StateVector(slice(0, 1))
        b = pybamm.StateVector(slice(1, 2))

        # test a * b
        known_symbols = OrderedDict()
        expr = a * b
        pybamm.find_symbols(expr, known_symbols)

        # test keys of known_symbols
        self.assertEqual(list(known_symbols.keys())[0], a.id)
        self.assertEqual(list(known_symbols.keys())[1], b.id)
        self.assertEqual(list(known_symbols.keys())[2], expr.id)

        # test values of known_symbols
        self.assertEqual(list(known_symbols.values())[0], 'y[0:1]')
        self.assertEqual(list(known_symbols.values())[1], 'y[1:2]')

        var_a = pybamm.id_to_python_variable(a.id)
        var_b = pybamm.id_to_python_variable(b.id)
        self.assertEqual(list(known_symbols.values())[
                         2], '{} * {}'.format(var_a, var_b))

        # test identical subtree
        known_symbols = OrderedDict()
        expr = a * b * b
        pybamm.find_symbols(expr, known_symbols)

        # test keys of known_symbols
        self.assertEqual(list(known_symbols.keys())[0], a.id)
        self.assertEqual(list(known_symbols.keys())[1], b.id)
        self.assertEqual(list(known_symbols.keys())[2], expr.children[0].id)
        self.assertEqual(list(known_symbols.keys())[3], expr.id)

        # test values of known_symbols
        self.assertEqual(list(known_symbols.values())[0], 'y[0:1]')
        self.assertEqual(list(known_symbols.values())[1], 'y[1:2]')
        self.assertEqual(list(known_symbols.values())[
                         2], '{} * {}'.format(var_a, var_b))

        var_child = pybamm.id_to_python_variable(expr.children[0].id)
        self.assertEqual(list(known_symbols.values())[
                         3], '{} * {}'.format(var_child, var_b))

        # test unary op
        known_symbols = OrderedDict()
        expr = a * (-b)
        pybamm.find_symbols(expr, known_symbols)

        # test keys of known_symbols
        self.assertEqual(list(known_symbols.keys())[0], a.id)
        self.assertEqual(list(known_symbols.keys())[1], b.id)
        self.assertEqual(list(known_symbols.keys())[2], expr.children[1].id)
        self.assertEqual(list(known_symbols.keys())[3], expr.id)

        # test values of known_symbols
        self.assertEqual(list(known_symbols.values())[0], 'y[0:1]')
        self.assertEqual(list(known_symbols.values())[1], 'y[1:2]')
        self.assertEqual(list(known_symbols.values())[2], '-{}'.format(var_b))
        var_child = pybamm.id_to_python_variable(expr.children[1].id)
        self.assertEqual(list(known_symbols.values())[3],
                         '{} * {}'.format(var_a, var_child))

        # test matrix
        known_symbols = OrderedDict()
        A = pybamm.Matrix(np.array([[1, 2], [3, 4]]))
        pybamm.find_symbols(A, known_symbols)
        self.assertEqual(list(known_symbols.keys())[0], A.id)
        self.assertEqual(list(known_symbols.values())[0], 'np.array([[1,2],[3,4]])')

        # test sparse matrix
        known_symbols = OrderedDict()
        A = pybamm.Matrix(scipy.sparse.csr_matrix(np.array([[0, 2], [0, 4]])))
        pybamm.find_symbols(A, known_symbols)
        self.assertEqual(list(known_symbols.keys())[0], A.id)
        self.assertEqual(list(known_symbols.values())[0],
                         'scipy.sparse.csr_matrix((np.array([2,4]), np.array([1,1]), np.array([0,1,2])),shape=(2,2))'
                         )

        # test numpy concatentate
        known_symbols = OrderedDict()
        expr = pybamm.NumpyConcatenation(a, b)
        pybamm.find_symbols(expr, known_symbols)
        self.assertEqual(list(known_symbols.keys())[0], a.id)
        self.assertEqual(list(known_symbols.keys())[1], b.id)
        self.assertEqual(list(known_symbols.keys())[2], expr.id)
        self.assertEqual(list(known_symbols.values())[2],
                         "np.concatenate(({},{}))".format(var_a, var_b)
                         )

        # test domain concatentate
        known_symbols = OrderedDict()
        expr = pybamm.NumpyConcatenation(a, b)
        pybamm.find_symbols(expr, known_symbols)
        self.assertEqual(list(known_symbols.keys())[0], a.id)
        self.assertEqual(list(known_symbols.keys())[1], b.id)
        self.assertEqual(list(known_symbols.keys())[2], expr.id)
        self.assertEqual(list(known_symbols.values())[2],
                         "np.concatenate(({},{}))".format(var_a, var_b)
                         )

        # test sparse stack
        known_symbols = OrderedDict()
        expr = pybamm.SparseStack(a, b)
        pybamm.find_symbols(expr, known_symbols)
        self.assertEqual(list(known_symbols.keys())[0], a.id)
        self.assertEqual(list(known_symbols.keys())[1], b.id)
        self.assertEqual(list(known_symbols.keys())[2], expr.id)
        self.assertEqual(list(known_symbols.values())[2],
                         "scipy.sparse.vstack(({},{}))".format(var_a, var_b)
                         )

    def test_domain_concatenation(self):
        disc = get_discretisation_for_testing()
        mesh = disc.mesh

        a_dom = ["negative electrode"]
        b_dom = ["positive electrode"]
        a = pybamm.Vector(2*np.ones_like(mesh[a_dom[0]][0].nodes), domain=a_dom)
        b = pybamm.Vector(np.ones_like(mesh[b_dom[0]][0].nodes), domain=b_dom)

        # concatenate them the "wrong" way round to check they get reordered correctly
        expr = pybamm.DomainConcatenation([b, a], mesh)

        known_symbols = OrderedDict()
        pybamm.find_symbols(expr, known_symbols)
        self.assertEqual(list(known_symbols.keys())[0], b.id)
        self.assertEqual(list(known_symbols.keys())[1], a.id)
        self.assertEqual(list(known_symbols.keys())[2], expr.id)

        var_a = pybamm.id_to_python_variable(a.id)
        var_b = pybamm.id_to_python_variable(b.id)
        a_pts = mesh[a_dom[0]][0].npts
        b_pts = mesh[b_dom[0]][0].npts
        self.assertEqual(list(known_symbols.values())[2],
                         "np.concatenate(({}[0:{}],{}[0:{}]))".format(
                             var_a, a_pts, var_b, b_pts)
                         )

        evaluator = pybamm.EvaluatorPython(expr)
        result = evaluator.evaluate()
        np.testing.assert_allclose(result, expr.evaluate())

        # check the reordering in case a child vector has to be split up
        a_dom = ["separator"]
        b_dom = ["negative electrode", "positive electrode"]
        a = pybamm.Vector(2*np.ones_like(mesh[a_dom[0]][0].nodes), domain=a_dom)
        b = pybamm.Vector(
            np.concatenate(
                [np.full(mesh[b_dom[0]][0].npts, 1), np.full(mesh[b_dom[1]][0].npts, 3)]
            )[:, np.newaxis],
            domain=b_dom,
        )
        var_a = pybamm.id_to_python_variable(a.id)
        var_b = pybamm.id_to_python_variable(b.id)
        expr = pybamm.DomainConcatenation([a, b], mesh)
        known_symbols = OrderedDict()
        pybamm.find_symbols(expr, known_symbols)

        b0_pts = mesh[b_dom[0]][0].npts
        a0_pts = mesh[a_dom[0]][0].npts
        b1_pts = mesh[b_dom[1]][0].npts

        b0_str = "{}[0:{}]".format(var_b, b0_pts)
        a0_str = "{}[0:{}]".format(var_a, a0_pts)
        b1_str = "{}[{}:{}]".format(var_b, b0_pts, b0_pts+b1_pts)

        self.assertEqual(list(known_symbols.values())[2],
                         "np.concatenate(({},{},{}))".format(b0_str, a0_str, b1_str)
                         )

        evaluator = pybamm.EvaluatorPython(expr)
        result = evaluator.evaluate()
        np.testing.assert_allclose(result, expr.evaluate())

    def test_to_python(self):
        a = pybamm.StateVector(slice(0, 1))
        b = pybamm.StateVector(slice(1, 2))

        # test a * b
        expr = a * b
        funct_str = pybamm.to_python(expr)
        expected_str = \
            "var_[0-9m]+ = y\[0:1\]\\n" \
            "var_[0-9m]+ = y\[1:2\]\\n" \
            "var_[0-9m]+ = var_[0-9m]+ \* var_[0-9m]+"

        self.assertRegex(funct_str, expected_str)

    def test_evaluator_python(self):
        a = pybamm.StateVector(slice(0, 1))
        b = pybamm.StateVector(slice(1, 2))

        y_tests = [np.array([[2], [3]]), np.array([[1], [3]])]
        t_tests = [1, 2]

        # test a * b
        expr = a * b
        evaluator = pybamm.EvaluatorPython(expr)
        result = evaluator.evaluate(t=None, y=np.array([[2], [3]]))
        self.assertEqual(result, 6)
        result = evaluator.evaluate(t=None, y=np.array([[1], [3]]))
        self.assertEqual(result, 3)

        # test a larger expression
        expr = a * b + b + a**2 / b + 2*a + b/2 + 4
        evaluator = pybamm.EvaluatorPython(expr)
        for y in y_tests:
            result = evaluator.evaluate(t=None, y=y)
            self.assertEqual(result, expr.evaluate(t=None, y=y))

        # test something with time
        expr = a * pybamm.t
        evaluator = pybamm.EvaluatorPython(expr)
        for t, y in zip(t_tests, y_tests):
            result = evaluator.evaluate(t=t, y=y)
            self.assertEqual(result, expr.evaluate(t=t, y=y))

        # test something with a matrix multiplication
        A = pybamm.Matrix(np.array([[1, 2], [3, 4]]))
        expr = A @ pybamm.StateVector(slice(0, 2))
        evaluator = pybamm.EvaluatorPython(expr)
        for t, y in zip(t_tests, y_tests):
            result = evaluator.evaluate(t=t, y=y)
            np.testing.assert_allclose(result, expr.evaluate(t=t, y=y))

        # test something with a sparse matrix multiplication
        A = pybamm.Matrix(np.array([[1, 2], [3, 4]]))
        B = pybamm.Matrix(scipy.sparse.csr_matrix(np.array([[1, 0], [0, 4]])))
        expr = A @ B @ pybamm.StateVector(slice(0, 2))
        evaluator = pybamm.EvaluatorPython(expr)
        for t, y in zip(t_tests, y_tests):
            result = evaluator.evaluate(t=t, y=y)
            np.testing.assert_allclose(result, expr.evaluate(t=t, y=y))

        # test numpy concatenation
        a = pybamm.Vector(np.array([[1], [2]]))
        b = pybamm.Vector(np.array([[3]]))
        expr = pybamm.NumpyConcatenation(a, b)
        evaluator = pybamm.EvaluatorPython(expr)
        for t, y in zip(t_tests, y_tests):
            result = evaluator.evaluate(t=t, y=y)
            np.testing.assert_allclose(result, expr.evaluate(t=t, y=y))

        # test sparse stack
        A = pybamm.Matrix(scipy.sparse.csr_matrix(np.array([[1, 0], [0, 4]])))
        B = pybamm.Matrix(scipy.sparse.csr_matrix(np.array([[2, 0], [5, 0]])))
        expr = pybamm.SparseStack(A, B)
        evaluator = pybamm.EvaluatorPython(expr)
        for t, y in zip(t_tests, y_tests):
            result = evaluator.evaluate(t=t, y=y).toarray()
            np.testing.assert_allclose(result, expr.evaluate(t=t, y=y).toarray())


if __name__ == "__main__":
    print("Add -v for more debug output")
    import sys

    if "-v" in sys.argv:
        debug = True
    unittest.main()

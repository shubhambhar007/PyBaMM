#
# Tests for surface-form lead-acid Newman-Tiedemann model
#
import pybamm
import unittest


class TestLeadAcidNewmanTiedemannSurfaceForm(unittest.TestCase):
    def test_well_posed(self):
        options = {"thermal": None, "Voltage": "On", "capacitance": False}
        model = pybamm.lead_acid.surface_form.NewmanTiedemann(options)
        model.check_well_posedness()

    def test_well_posed_with_capacitance(self):
        options = {"thermal": None, "Voltage": "On", "capacitance": True}
        model = pybamm.lead_acid.surface_form.NewmanTiedemann(options)
        model.check_well_posedness()

    @unittest.skipIf(pybamm.have_scikits_odes(), "scikits.odes not installed")
    def test_default_solver(self):

        options = {"thermal": None, "Voltage": "On", "capacitance": False}
        model = pybamm.lead_acid.surface_form.NewmanTiedemann(options)
        self.assertIsInstance(model.default_solver, pybamm.ScikitsDaeSolver)

        options = {"thermal": None, "Voltage": "On", "capacitance": True}
        model = pybamm.lead_acid.surface_form.NewmanTiedemann(options)
        self.assertIsInstance(model.default_solver, pybamm.ScikitsOdeSolver)


if __name__ == "__main__":
    print("Add -v for more debug output")
    import sys

    if "-v" in sys.argv:
        debug = True
    unittest.main()
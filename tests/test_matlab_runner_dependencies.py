import pytest

from models.pvmaps.matlab_runner import _validate_matlab_dependencies


class FakeMatlabEngine:
    def __init__(self, has_network_class):
        self.has_network_class = has_network_class
        self.calls = []

    def eval(self, expression, nargout):
        self.calls.append((expression, nargout))
        return self.has_network_class


@pytest.mark.parametrize("cell_tech", ["AL_BSF", "BI_PERC", "SHJ", "SHJ_NN"])
def test_standard_cell_technologies_do_not_require_network_toolbox(cell_tech):
    engine = FakeMatlabEngine(has_network_class=False)

    _validate_matlab_dependencies(engine, cell_tech)

    assert engine.calls == []


@pytest.mark.parametrize("cell_tech", ["PVK_SI_2T", "PVK_SI_4T"])
def test_tandem_cell_technologies_require_network_toolbox(cell_tech):
    engine = FakeMatlabEngine(has_network_class=False)

    with pytest.raises(RuntimeError, match="Deep Learning Toolbox"):
        _validate_matlab_dependencies(engine, cell_tech)


@pytest.mark.parametrize("cell_tech", ["PVK_SI_2T", "PVK_SI_4T"])
def test_tandem_cell_technologies_run_when_network_toolbox_is_available(cell_tech):
    engine = FakeMatlabEngine(has_network_class=True)

    _validate_matlab_dependencies(engine, cell_tech)

    assert engine.calls == [("~isempty(which('network'))", 1)]

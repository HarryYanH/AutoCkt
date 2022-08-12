""" 
# Hdl21 Built-In Generators 
# Unit Tests 
"""

import hdl21 as h


def test_mos_generator():
    """Initial test of built-in series-Mos generator"""

    Mos = h.generators.Mos
    m = Mos(Mos.Params(nser=2))

    assert isinstance(m, h.GeneratorCall)
    assert isinstance(m.params, Mos.Params)

    m = h.elaborate(m)

    assert isinstance(m, h.Module)
    assert len(m.ports) == 4
    assert m.ports.keys() == h.primitives.Mos.ports.keys()
    assert len(m.instances) == 2
    assert "unit0" in m.instances
    assert "unit1" in m.instances
    assert isinstance(m.instances["unit0"].of, h.PrimitiveCall)
    assert isinstance(m.instances["unit1"].of, h.PrimitiveCall)
    assert m.instances["unit0"].of.params == h.primitives.MosParams()
    assert m.instances["unit1"].of.params == h.primitives.MosParams()
    assert len(m.signals) == 1
    assert "unit0_d" in m.signals


def test_series_parallel_generator():
    """Initial test of the general-purpose series-parallel generator"""

    from hdl21.generators import SeriesPar

    @h.module
    class M:  # Unit cell
        a, b, c, d, e, f, g = h.Ports(7)

    params = SeriesPar.Params(unit=M, npar=2, nser=2, series_conns=["a", "b"])
    m = SeriesPar(params)

    assert isinstance(m, h.GeneratorCall)
    assert isinstance(m.params, SeriesPar.Params)

    m = h.elaborate(m)

    assert isinstance(m, h.Module)
    assert len(m.ports) == 7
    assert m.ports.keys() == M.ports.keys()
    assert len(m.instances) == 4
    assert "unit_0_0" in m.instances
    assert "unit_0_1" in m.instances
    assert "unit_1_0" in m.instances
    assert "unit_1_1" in m.instances

    for inst in m.instances.values():
        assert inst.of is M
    assert len(m.signals) == 2
    assert "unit_0_0_b" in m.signals
    assert "unit_1_0_b" in m.signals

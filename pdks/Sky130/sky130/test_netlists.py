"""
This series of tests is made by painstaklingly checking each generated
SPICE file against the correct NgSpice netlist generated by Xschem
to ensure that the generated files have the following properties:

1) Ports are being mapped correctly from physical meaning to SPICE param
2) Primitives and params are passing the correct params to the SPICE file
3) SPICE files aren't breaking design constraints (eg. some resistors have
   no explicit width)
"""

from io import StringIO

import hdl21 as h
from hdl21.prefix import µ
import sky130  # No weird or illegal parameters...


def test_xtor_netlists():
    """
    Explicitly check xtor netlists to see that nothing
    illegal is being generated and that models are compliant
    with pre-defined PDK behaviour
    """

    @h.generator
    def GenXtor(params: h.MosParams) -> h.Module:
        @h.module
        class SingleXtor:

            a, b, c, d = 4 * h.Signal()
            xtor = h.Mos(params)(d=a, g=b, s=c, b=d)

        return SingleXtor

    for x in sky130.xtors.keys():

        # Relevant params
        p = h.MosParams(model=x[0], tp=x[1], vth=x[2], w=30 * µ, l=30 * µ)

        # Generate & Compile
        mod = h.elaborate(GenXtor(p))
        sky130.compile(mod)

        # Netlist and compare
        s = StringIO()

        # Ignore the iso model, its not used in the test
        if sky130.xtors[x].name != "sky130_fd_pr__nfet_20v0_iso":

            h.netlist(mod, dest=s, fmt="spice")
            s = s.getvalue().split("\n")

            assert s[9] == "+ a b c d "  # Correctly maps ports to their places...
            assert s[10] == "+ " + sky130.xtors[x].name + " "  # Has correct PDK name...

            if "20v" not in sky130.xtors[x].name:

                assert (
                    s[11]
                    == "+ w='30' \
l='30' \
nf='1' \
ad='int((nf+1)/2) * w/nf * 0.29' \
As='int((nf+2)/2) * w/nf * 0.29' \
pd='2*int((nf+1)/2) * (w/nf + 0.29)' \
ps='2*int((nf+2)/2) * (w/nf + 0.29)' \
nrd='0.29 / w' \
nrs='0.29 / w' \
sa='0' \
sb='0' \
sd='0' \
mult='1' \
m='1' "
                )  # No weird or illegal parameters...

            else:

                assert s[11] == "+ w='30' l='30' m='1' "


def test_2_term_res_netlists():
    """
    Explicitly check generic resistor netlists to see that nothing
    illegal is being generated and that models are compliant
    with pre-defined PDK behaviour
    """

    @h.generator
    def GenRes(params: h.PhysicalResistorParams) -> h.Module:
        @h.module
        class SingleRes:

            a, b = 2 * h.Signal()
            genres = h.PhysicalResistor(params)(p=a, n=b)

        return SingleRes

    for x in sky130.ress.keys():

        # This is a hackish way to isolate the two terminal resistors
        if len(sky130.ress[x].port_list) == 2:

            # Relevant params
            p = h.PhysicalResistorParams(model=x, w=10 * µ, l=10 * µ)

            # Generate & Compile
            mod = h.elaborate(GenRes(p))
            sky130.compile(mod)

            # Netlist and compare
            s = StringIO()
            h.netlist(mod, dest=s, fmt="spice")
            s = s.getvalue().split("\n")

            assert s[9] == "+ a b "  # Correctly maps ports to their places...
            assert s[10] == "+ " + sky130.ress[x].name + " "  # Has correct PDK name...
            assert (
                s[11] == "+ w='10' l='10' m='1' "
            )  # No weird or illegal parameters...


def test_3_term_res_netlists():
    """
    Explicitly check precision resistor netlists to see that nothing
    illegal is being generated and that models are compliant
    with pre-defined PDK behaviour
    """

    @h.generator
    def GenRes(params: h.PhysicalResistorParams) -> h.Module:
        @h.module
        class SingleRes:

            x, y, z = 3 * h.Signal()
            genres = h.ThreeTerminalResistor(params)(p=x, n=y, b=z)

        return SingleRes

    for x in sky130.ress.keys():

        if len(sky130.ress[x].port_list) == 3:

            # Relevant params
            p = h.PhysicalResistorParams(model=x, w=10 * µ, l=10 * µ)

            # Generate & Compile
            mod = h.elaborate(GenRes(p))
            sky130.compile(mod)

            # Netlist and compare
            s = StringIO()
            h.netlist(mod, dest=s, fmt="spice")
            s = s.getvalue().split("\n")

            name = sky130.ress[x].name

            # Are you a generic resistor??
            if x.startswith("GEN"):

                assert s[9] == "+ x y z "  # Correctly maps ports to their places
                assert s[10] == "+ " + name + " "  # Has correct PDK name
                assert (
                    s[11] == f"+ w='10' l='10' m='1' "
                )  # No weird or illegal parameters...

            else:

                fixed_length = float(sky130.default_prec_res_L[name].inner)

                assert s[9] == "+ x y z "  # Correctly maps ports to their places
                assert s[10] == "+ " + name + " "  # Has correct PDK name
                assert (
                    s[11] == f"+ l='{fixed_length}' mult='1' m='1' "
                )  # No weird or illegal parameters...


def test_diode_netlists():

    """
    Explicitly check diode netlists to see that nothing
    illegal is being generated and that models are compliant
    with pre-defined PDK behaviour
    """

    @h.generator
    def GenDiode(params: h.DiodeParams) -> h.Module:
        @h.module
        class SingleDiode:

            x, y = 2 * h.Signal()
            gendiode = h.Diode(params)(p=x, n=y)

        return SingleDiode

    for x in sky130.diodes.keys():

        # Relevant param
        p = h.DiodeParams(model=x, w=3, l=3)

        # Generate and compile
        mod = h.elaborate(GenDiode(p))
        sky130.compile(mod)

        # Netlist and compare
        s = StringIO()
        h.netlist(mod, dest=s, fmt="spice")
        s = s.getvalue().split("\n")

        assert s[9] == "+ x y "  # Correctly maps ports to their places...
        assert s[10] == "+ " + sky130.diodes[x].name + " "  # Has correct PDK name...
        assert s[11] == "+ area='9T' pj='12M' "  # No weird or illegal parameters...


def test_pnp_netlists():
    @h.generator
    def GenBipolar(params: h.BipolarParams) -> h.Module:
        @h.module
        class SingleBipolar:

            x, y, z = 3 * h.Signal()
            genBipolar = h.Bipolar(params)(c=x, b=y, e=z)

        return SingleBipolar

    for x in sky130.bjts.keys():

        if x.startswith("PNP"):
            # Relevant param
            p = h.BipolarParams(model=x)

            # Generate and compile
            mod = h.elaborate(GenBipolar(p))
            sky130.compile(mod)

            # Netlist and compare
            s = StringIO()
            h.netlist(mod, dest=s, fmt="spice")
            s = s.getvalue().split("\n")

            assert s[9] == "+ x y z "  # Correctly maps ports to their places...
            assert s[10] == "+ " + sky130.bjts[x].name + " "  # Has correct PDK name...
            assert s[11] == "+ m='1' "  # No weird or illegal parameters...


def test_npn_netlists():

    p = sky130.Sky130BipolarParams()

    @h.module
    class Bipolar1:

        w, x, y, z = 4 * h.Signal()
        genBipolar = sky130.modules.NPN_5p0V_1x2(p)(c=w, b=x, e=y, s=z)

    @h.module
    class Bipolar2:

        w, x, y, z = 4 * h.Signal()
        genBipolar = sky130.modules.NPN_5p0V_1x1(p)(c=w, b=x, e=y, s=z)

    s = StringIO()
    h.netlist(Bipolar1, dest=s, fmt="spice")
    s = s.getvalue().split("\n")

    assert s[9] == "+ w x y z "  # Correctly maps ports to their places...
    assert s[10] == "+ sky130_fd_pr__npn_05v5_W1p00L2p00 "  # Has correct PDK name...
    assert s[11] == "+ m='1' "  # No weird or illegal parameters...

    s = StringIO()
    h.netlist(Bipolar2, dest=s, fmt="spice")
    s = s.getvalue().split("\n")

    assert s[9] == "+ w x y z "  # Correctly maps ports to their places...
    assert s[10] == "+ sky130_fd_pr__npn_05v5_W1p00L1p00 "  # Has correct PDK name...
    assert s[11] == "+ m='1' "  # No weird or illegal parameters...


def test_mim_cap_netlists():
    @h.generator
    def GenMimCap(params: h.PhysicalCapacitorParams) -> h.Module:
        @h.module
        class SingleCap:

            x, y = 2 * h.Signal()
            genCap = h.PhysicalCapacitor(params)(p=x, n=y)

        return SingleCap

    for x in sky130.caps.keys():

        if x.startswith("MIM"):

            # Relevant params
            p = h.PhysicalCapacitorParams(model=x, w=3 * µ, l=3 * µ)

            # Generate and compile
            mod = h.elaborate(GenMimCap(p))
            sky130.compile(mod)

            # Netlist and compare
            s = StringIO()
            h.netlist(mod, dest=s, fmt="spice")
            s = s.getvalue().split("\n")

            assert s[9] == "+ x y "  # Correctly maps ports to their places...
            assert s[10] == "+ " + sky130.caps[x].name + " "  # Has correct PDK name...
            assert s[11] == "+ w='3' l='3' mf='1' "  # No weird or illegal parameters...


def test_var_cap_netlists():
    @h.generator
    def GenMimCap(params: h.PhysicalCapacitorParams) -> h.Module:
        @h.module
        class SingleCap:

            x, y, z = 3 * h.Signal()
            genCap = h.ThreeTerminalCapacitor(params)(p=x, n=y, b=z)

        return SingleCap

    for x in sky130.caps.keys():

        if x.startswith("VAR"):

            # Relevant params
            p = h.PhysicalCapacitorParams(model=x, w=3 * µ, l=3 * µ)

            # Generate and compile
            mod = h.elaborate(GenMimCap(p))
            sky130.compile(mod)

            # Netlist and compare
            s = StringIO()
            h.netlist(mod, dest=s, fmt="spice")
            s = s.getvalue().split("\n")

            assert s[9] == "+ x y z "  # Correctly maps ports to their places...
            assert s[10] == "+ " + sky130.caps[x].name + " "  # Has correct PDK name...
            assert s[11] == "+ w='3' l='3' vm='1' "  # No weird or illegal parameters...


def test_vpp_cap_netlists():
    @h.generator
    def T3VPPCap(params: h.PhysicalCapacitorParams) -> h.Module:
        @h.module
        class SingleCap:

            x, y, z = 3 * h.Signal()
            genCap = h.ThreeTerminalCapacitor(params)(p=x, n=y, b=z)

        return SingleCap

    for x in sky130.vpps.keys():

        if x.startswith("VPP_PARA"):

            p = sky130.Sky130VPPParams(w=3, l=3)

            @h.module
            class SingleCap:

                a, b, c = 3 * h.Signal()
                exec(f"genCap = sky130.modules.{x}")
                Cap = genCap(p)(p=a, n=b, b=c)

            # Generate
            mod = SingleCap
            sky130.compile(mod)

            # Netlist and compare
            s = StringIO()
            h.netlist(mod, dest=s, fmt="spice")
            s = s.getvalue().split("\n")

            assert s[9] == "+ a b c "  # Correctly maps ports to their places...
            assert s[10] == "+ " + sky130.vpps[x].name + " "  # Has correct PDK name...
            assert s[11] == "+ w='3' l='3' mult='1' m='1' "

        if x.startswith("VPP_PERP"):

            p = sky130.Sky130VPPParams(w=3, l=3)

            @h.module
            class SingleCap:

                a, b, c, d = 4 * h.Signal()
                exec(f"genCap = sky130.modules.{x}")
                Cap = genCap(p)(p=a, n=b, t=c, b=d)

            # Generate
            mod = SingleCap
            sky130.compile(mod)

            # Netlist and compare
            s = StringIO()
            h.netlist(mod, dest=s, fmt="spice")
            s = s.getvalue().split("\n")

            assert s[9] == "+ a b c d "  # Correctly maps ports to their places...
            assert s[10] == "+ " + sky130.vpps[x].name + " "  # Has correct PDK name...
            assert s[11] == "+ w='3' l='3' mult='1' m='1' "

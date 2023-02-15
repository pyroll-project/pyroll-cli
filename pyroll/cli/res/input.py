import pyroll.core as pr

# initial profile
in_profile = pr.Profile.round(
    diameter=30e-3,
    temperature=1200 + 273.15,
    strain=0,
    material=["C45", "steel"],
    flow_stress=40e6,
    density=7.7e3,
    thermal_capacity=465,
    thermal_conductivity=23,
)

# pass sequence
sequence = pr.PassSequence([
    pr.RollPass(
        label="Oval I",
        roll=pr.Roll(
            groove=pr.CircularOvalGroove(
                r1=6e-3,
                r2=40e-3,
                depth=8e-3,
            ),
            nominal_radius=160e-3,
            rotational_frequency=1
        ),
        gap=2e-3,
    ),
    pr.Transport(
        label="I => II",
        duration=1
    ),
    pr.RollPass(
        label="Round II",
        roll=pr.Roll(
            groove=pr.RoundGroove(
                r1=1e-3,
                r2=12.5e-3,
                depth=11.5e-3
            ),
            nominal_radius=160e-3,
            rotational_frequency=1
        ),
        gap=2e-3,
    ),
])

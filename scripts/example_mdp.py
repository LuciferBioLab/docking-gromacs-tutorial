"""Materialize the small example's stage-specific GROMACS parameters."""

import argparse
from pathlib import Path

COMMON = {
    "cutoff-scheme": "Verlet", "coulombtype": "PME", "rcoulomb": 1.0,
    "vdwtype": "Cut-off", "rvdw": 1.0, "DispCorr": "EnerPres", "pbc": "xyz",
}


def write_mdp(path, settings):
    with path.open("x") as handle:
        for key, value in settings.items():
            handle.write(f"{key:<22} = {value}\n")


def create(out, profile, seed):
    out.mkdir(exist_ok=True)
    quick = profile == "quickstart"
    # Smoke stages test data and software handoff. They do not establish physical equilibration.
    em = COMMON | {"integrator": "steep", "nsteps": 1500, "emtol": 1000, "emstep": 0.01}
    ions = em | {"coulombtype": "Cut-off", "nsteps": 500}
    dynamics = COMMON | {
        "integrator": "md", "dt": 0.002, "tcoupl": "V-rescale", "tc-grps": "System",
        "tau-t": 1.0, "ref-t": 300, "constraint-algorithm": "lincs", "constraints": "h-bonds",
        "nstenergy": 100, "nstlog": 100, "nstxout-compressed": 100,
    }
    nvt = dynamics | {
        "nsteps": 25000 if quick else 500,
        "define": "-DPOSRES -DPOSRES_LIG", "pcoupl": "no",
        "gen-vel": "yes", "gen-temp": 300, "gen-seed": seed, "continuation": "no",
    }
    barostat = {
        "pcoupl": "C-rescale", "pcoupltype": "isotropic",
        "tau-p": 5.0, "ref-p": 1.0, "compressibility": 4.5e-5, "continuation": "yes",
    }
    npt = dynamics | barostat | {
        "nsteps": 50000 if quick else 500, "define": "-DPOSRES -DPOSRES_LIG",
        "refcoord-scaling": "com",
    }
    md = dynamics | barostat | {"nsteps": 500000 if quick else 1000, "nstxout-compressed": 500 if quick else 100}
    for name, settings in (("ions", ions), ("em", em), ("nvt", nvt), ("npt", npt), ("md", md)):
        write_mdp(out / f"{name}.mdp", settings)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("profile", choices=["smoke", "quickstart"])
    parser.add_argument("seed", type=int)
    args = parser.parse_args()
    create(args.directory, args.profile, args.seed)

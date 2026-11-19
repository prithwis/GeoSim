
# ============================================================
# gsWorld.py
# GeoSim - World Variables and WorldState
# ============================================================

import json
from pathlib import Path
from dataclasses import dataclass, field
from copy import deepcopy


# ------------------------------------------------------------
# WorldVariable
# ------------------------------------------------------------

#from dataclasses import dataclass, field

@dataclass
class WorldVariable:
    name: str
    description: str
    direction: str
    index: float = 100.0
    status: str = ""
    rationale: str = ""
    conditions: list[str] = field(default_factory=list)


# ------------------------------------------------------------
# Load variable definitions from external JSON
# ------------------------------------------------------------

def loadWorldVariables(variable_file):
    """
    Load an arbitrary number of WorldVariable definitions.
    """

    data = json.loads(
        Path(variable_file).read_text(encoding="utf-8")
    )

    variables = [
        WorldVariable(**item)
        for item in data["variables"]
    ]

    names = [v.name for v in variables]

    if len(names) != len(set(names)):
        raise ValueError("Duplicate WorldVariable names")

    if not variables:
        raise ValueError("No WorldVariables defined")

    return variables


# ------------------------------------------------------------
# WorldState
# ------------------------------------------------------------

class WorldState:
    """
    Snapshot of all world variables at one simulation epoch.

    Each epoch is represented by a separate WorldState instance.
    """

    def __init__(self, variables, values=None):

        self.variables = deepcopy(list(variables))

        if values is None:
            self.values = {
                v.name: v.index
                for v in self.variables
            }
        else:
            self.values = deepcopy(dict(values))

        self.validate()

    def validate(self):
        """
        Validate variable names and numerical values.
        """

        names = [v.name for v in self.variables]

        if len(names) != len(set(names)):
            raise ValueError("Duplicate WorldVariable names")

        if set(self.values) != set(names):
            raise ValueError("WorldState variable mismatch")

        for name, value in self.values.items():
            if isinstance(value, bool) or not isinstance(
                value, (int, float)
            ):
                raise ValueError(
                    f"{name}: value must be numeric"
                )

    def as_dict(self):
        return deepcopy(self.values)

    def __repr__(self):
        return f"WorldState({self.values})"

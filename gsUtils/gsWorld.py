
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

@dataclass
class WorldState:
    state_id: str
    variables: list[WorldVariable] = field(default_factory=list)

# -------------------   
    def to_json(self):
        return json.dumps(
            self,
            default=lambda o: o.__dict__,
            indent=2
        )
# -------------------   
    @classmethod
    def from_dict(cls, data):
        variables = [
            WorldVariable(**v)
            for v in data["variables"]
        ]

        return cls(
            state_id=data["state_id"],
            variables=variables
        )
# -------------------        
    def show(self, n=-1):
        """
        Display a WorldState at different levels of detail.

        n = -2       : vector values only
        n = -1       : vector names and values (default)
        0 <= n < N   : complete details of vector n
        n >= N       : complete details of all vectors
        """

        variables = self.variables
        N = len(variables)

        # ---------------------------------------------------------
        # -2 : Values only
        # ---------------------------------------------------------
        if n == -2:
            print([v.index for v in variables])
            return


        # ---------------------------------------------------------
        # -1 : Names and values (default)
        # ---------------------------------------------------------
        if n == -1:

            print(f"\nWorld State : {self.state_id}")
            print("-" * 55)

            for i, v in enumerate(variables):
                print(f"{i:2d}  {v.name:<32} {v.index:8.2f}")

            return


        # ---------------------------------------------------------
        # Helper for detailed display
        # ---------------------------------------------------------
        def show_variable(i):

            v = variables[i]

            print(f"\nVector {i} : {v.name}")
            print("-" * 70)

            print(f"Index       : {v.index}")
            print(f"Description : {v.description}")
            print(f"Direction   : {v.direction}")
            print(f"Status      : {v.status}")
            print(f"Rationale   : {v.rationale}")
            print("Conditions  :")

            if v.conditions:
                for condition in v.conditions:
                    print(f"  - {condition}")
            else:
                print("  - None")


        # ---------------------------------------------------------
        # 0 ... N-1 : Complete details of one vector
        # ---------------------------------------------------------
        if 0 <= n < N:

            print(f"\nWorld State : {self.state_id}")
            show_variable(n)
            return


        # ---------------------------------------------------------
        # N or greater : Complete details of all vectors
        # ---------------------------------------------------------
        if n >= N:

            print(f"\nWorld State : {self.state_id}")
            print("=" * 70)

            for i in range(N):
                show_variable(i)

            return


        # ---------------------------------------------------------
        # Less than -2 : invalid
        # ---------------------------------------------------------
        print(f"Invalid show parameter: {n}")

# =============================================================================     




@dataclass
class Event:
    actor: str
    action: str
    rationale: str = ""
    event_id: str = ""
    selection_weight: float | None = None

    def show(self):
        #print(f"Event     : {self.event_id}")
        print(f"\nEvent : {self.event_id}")
        print("-" * 55)
        print(f"Actor     : {self.actor}")
        print(f"Action    : {self.action}")
        print(f"Rationale : {self.rationale}")
        print(f"selection_weight : {self.selection_weight}")
        
#      '''  
#    def to_json(self):
#        return json.dumps(
#            self,
#            default=lambda o: o.__dict__,
#            indent=2
#        )
#        '''
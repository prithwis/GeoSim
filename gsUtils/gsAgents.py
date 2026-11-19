
# ============================================================
# gsAgents.py
# GeoSim - LLM Agent Classes
# ============================================================

from gsLLM import callLLM


# ------------------------------------------------------------
# Base Agent
# ------------------------------------------------------------

class Agent:
    """
    Base class for all LLM-driven GeoSim agents.

    Handles:
        - LLM client
        - Role instructions
        - Model and provider selection
        - Reasoning effort
        - LLM invocation
    """

    def __init__(
        self,
        client,
        role,
        model,
        provider,
        effort="medium"
    ):
        self.client = client
        self.role = role
        self.model = model
        self.provider = provider
        self.effort = effort

    def ask(self, query):
        """
        Send a query to the configured LLM.
        """
        return callLLM(
            self.client,
            self.role,
            query,
            model=self.model,
            provider=self.provider,
            effort=self.effort
        )


# ------------------------------------------------------------
# ZeitWorld
# ------------------------------------------------------------

class ZeitWorld(Agent):
    """
    Maintains the simulated world.

    Responsibilities:
        1. Initialise W[0].
        2. Generate W[t+1] from W[t] and a selected event.
    """

    def initialise(self, variables, world_facts, init_prompt):
        import json
        from dataclasses import asdict
        from gsWorld import WorldState

        self.initialised = False

        # Construct the WorldState template
        template = {
            "variables": [asdict(v) for v in variables]
        }

        query = (
            f"{init_prompt}\n\n"
            "WORLDSTATE TEMPLATE\n"
            f"{json.dumps(template, indent=2, ensure_ascii=False)}\n\n"
            "WORLD FACTS\n"
            f"{world_facts}"
        )

        # Actual LLM call
        response = self.ask(query)

        # Accept JSON returned inside a Markdown code fence
        response = response.strip()
        if response.startswith("```"):
            response = response.split("\n", 1)[1]
            response = response.rsplit("```", 1)[0].strip()

        result = json.loads(response)

        # Validate the returned WorldState
        returned = result["variables"]

        if len(returned) != len(variables):
            raise ValueError("ZeitWorld returned incorrect variable count")

        required = {
            "name", "description", "direction", "index",
            "status", "rationale", "conditions"
        }

        for original, completed in zip(variables, returned):

            if set(completed) != required:
                raise ValueError(
                    f"Incorrect fields for {original.name}"
                )

            for key in ("name", "description", "direction"):
                if completed[key] != getattr(original, key):
                    raise ValueError(
                        f"{original.name}: {key} was modified"
                    )

            if type(completed["index"]) not in (int, float) or completed["index"] != 100:
                raise ValueError(
                    f"{original.name}: initial index must be 100"
                )

            if not isinstance(completed["status"], str):
                raise ValueError("Invalid status")

            if not isinstance(completed["rationale"], str):
                raise ValueError("Invalid rationale")

            if not isinstance(completed["conditions"], list) or not all(
                isinstance(c, str) for c in completed["conditions"]
            ):
                raise ValueError("Invalid conditions")

        # Convert completed dictionaries to WorldVariable objects
        from gsWorld import WorldVariable

        completed_variables = [
            WorldVariable(**item) for item in returned
        ]

        # WorldState must retain these completed variables
        W0 = WorldState(completed_variables)

        self.initialised = True
        return W0

    def evolve(self, current_state, event):
        """
        Generate the next WorldState after an event.
        """
        raise NotImplementedError


# ------------------------------------------------------------
# Chanakya
# ------------------------------------------------------------

class Chanakya(Agent):
    """
    Proposes candidate geopolitical events.

    Different Chanakya instances may represent different
    countries, strategic perspectives or LLM providers.
    """

    def propose(self, world_state):
        """
        Generate candidate events from the current WorldState.
        """
        raise NotImplementedError


# ------------------------------------------------------------
# Centaur
# ------------------------------------------------------------

class Centaur(Agent):
    """
    Evaluates candidate events and assigns likelihoods.
    """

    def evaluate(self, world_state, events):
        """
        Assign likelihood weights to candidate events.
        """
        raise NotImplementedError

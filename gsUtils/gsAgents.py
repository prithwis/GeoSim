
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

    def initialise(self, variables, world_facts):
        """
        Construct the initial WorldState.

        Implementation will use the WorldState class
        defined in gsWorld.py.
        """
        raise NotImplementedError

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

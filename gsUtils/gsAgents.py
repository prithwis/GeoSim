
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


class Actor(Agent):
    def __init__(self, client, model, provider,
                 actor_id, name, description, role,
                 actor_type="LLM", email=None,
                 effort="medium"):

        super().__init__(client, role, model, provider, effort)

        self.actor_id = actor_id
        self.name = name
        self.description = description
        self.role = role
        self.actor_type = actor_type
        self.email = email

    def show(self):

        print(f"Actor ID    : {self.actor_id}")
        print(f"Name        : {self.name}")
        print(f"Description : {self.description}")
        print(f"Type        : {self.actor_type}")


    # --------------------------------------------------------
    # Convert Trigger Event to text
    # --------------------------------------------------------

    def _event_to_text(self, event):

        return f"""
        Event ID  : {event.event_id}
        Actor     : {event.actor}
        Action    : {event.action}
        Rationale : {event.rationale}
        """.strip()


    # --------------------------------------------------------
    # Convert WorldState to text
    # --------------------------------------------------------

    def _world_to_text(self, world):
        """
        Convert the current WorldState into compact text
        suitable for strategic reasoning.

        Chanakya receives:
            - variable name
            - index
            - status
            - surviving conditions

        ZeitWorld's transition rationale is deliberately
        excluded.
        """

        lines = [
            f"WorldState: {world.state_id}",
            ""
        ]

        for v in world.variables:

            lines.append(f"VARIABLE: {v.name}")
            lines.append(f"Index: {v.index}")
            lines.append(f"Status: {v.status}")

            if v.conditions:

                lines.append("Conditions:")

                for condition in v.conditions:
                    lines.append(f"- {condition}")

            lines.append("")

        return "\n".join(lines)
    
    
    def propose(self, W, E, propose_prompt):
        raise NotImplementedError


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
    def __init__(self, client, role, model, provider, effort="medium"):
            super().__init__(client, role, model, provider, effort)
            self.initialised = False

    def initialise(self, variables, world_facts, init_prompt):
        import json
        from dataclasses import asdict
        from gsWorld import WorldState

        #self.initialised = False

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
        print(json.dumps(result["variables"][2], indent=2))

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
        #W0 = WorldState(completed_variables)
        W0 = WorldState("W0", completed_variables)

        self.initialised = True
        return W0
# -------------            

   
    def update(self, world_list, event, update_prompt):
        """
        Apply an executed Event to the current WorldState,
        create W[t+1], append it to world_list,
        and return the new WorldState.
        """

        import json
        from gsWorld import WorldState

        if not self.initialised:
            raise RuntimeError(
                "ZeitWorld must be initialised before update."
            )

        current_state = world_list[-1]
        print("ZeitWorld Updating WorldState ----------", current_state.state_id)

        current_number = int(current_state.state_id[1:])
        next_state_id = f"W{current_number + 1}"

        # Build complete runtime input
        full_input = f"""
        {update_prompt}

        CURRENT WORLDSTATE
        ==================
        {current_state.to_json()}

        EXECUTED EVENT
        ==============
        Actor     : {event.actor}
        Action    : {event.action}
        Rationale : {event.rationale}
        """

        # Ask ZeitWorld to calculate the new state
        response = self.ask(full_input)

        # Accept JSON inside Markdown code fences
        response = response.strip()
        if response.startswith("```"):
            response = response.split("\n", 1)[1]
            response = response.rsplit("```", 1)[0].strip()

        data = json.loads(response)
        new_state = WorldState.from_dict(data)

        # Python controls state identity
        new_state.state_id = next_state_id

        # Successfully generated state becomes history
        #world_list.append(new_state)
        print("Generated WorldState ----------", new_state.state_id)

        return new_state

# =============================================================================

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

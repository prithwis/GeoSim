
# ============================================================
# gsActors.py
# GeoSim - LLM Agent Classes
# ============================================================

from gsLLM import callLLM

class Actor:
    def __init__(self, client, model, provider,
                 actor_id, name, description, role,
                 actor_type="LLM", email=None,
                 effort="medium"):

        self.client = client
        self.role = role
        self.model = model
        self.provider = provider
        self.effort = effort

        self.actor_id = actor_id
        self.name = name
        self.description = description
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
    
    
    
    def propose(self, W, E, generic_role, propose_prompt):
        """
        Generate alternative Event proposals for this Actor.

        The number and nature of proposals are determined
        by propose_prompt.

        Does not select, execute, or append any Event.
        """

        import json
        from gsWorld import Event

        # --------------------------------------------------------
        # Prepare current simulation context
        # --------------------------------------------------------

        trigger_text = self._event_to_text(E[-1])
        world_text = self._world_to_text(W[-1])

        # --------------------------------------------------------
        # System Prompt
        # Generic role + Actor-specific role
        # --------------------------------------------------------

        system_prompt = f"""
    GENERIC ACTOR ROLE
    ==================
    {generic_role}

    SPECIFIC ACTOR ROLE
    ===================
    Actor ID : {self.actor_id}
    Actor    : {self.name}

    {self.role}
    """.strip()

        # --------------------------------------------------------
        # User Prompt
        # Latest Event + Current WorldState + Strategy
        # --------------------------------------------------------

        user_prompt = f"""
    LATEST EVENT
    ============
    {trigger_text}

    CURRENT WORLDSTATE
    ==================
    {world_text}

    PROPOSAL STRATEGY
    =================
    {propose_prompt}

    TASK
    ====
    Generate alternative strategic responses available
    to {self.name} in the current situation.

    Follow the PROPOSAL STRATEGY instructions regarding
    the number, nature and orientation of alternatives.

    For each alternative provide:
    - action
    - rationale

    Do NOT choose among alternatives.
    Do NOT rank alternatives.
    Do NOT assign probabilities.
    Do NOT update the WorldState.
    Do NOT predict numerical changes to WorldState variables.

    OUTPUT FORMAT
    =============
    Return ONLY valid JSON as a list.

    Each element must have this structure:

    {{
        "action": "...",
        "rationale": "..."
    }}
    """.strip()

        # --------------------------------------------------------
        # Call LLM
        # --------------------------------------------------------

        response = callLLM(
            self.client,
            system_prompt,
            user_prompt,
            model=self.model,
            provider=self.provider,
            effort=self.effort
        )

        # --------------------------------------------------------
        # Parse JSON response
        # --------------------------------------------------------

        if isinstance(response, str):
            response = response.strip()

            if response.startswith("```"):
                response = response.split("\n", 1)[1]
                response = response.rsplit("```", 1)[0].strip()

            data = json.loads(response)
        else:
            data = response

        # --------------------------------------------------------
        # Validate response structure
        # --------------------------------------------------------

        if not isinstance(data, list):
            raise ValueError("Actor proposals must be a JSON list")

        # --------------------------------------------------------
        # Convert proposals into Event objects
        # --------------------------------------------------------

        options = []

        for item in data:

            if not isinstance(item, dict):
                raise ValueError("Invalid Event proposal")

            if not all(
                isinstance(item.get(k), str) and item[k].strip()
                for k in ("action", "rationale")
            ):
                raise ValueError("Invalid action or rationale")

            options.append(
                Event(
                    actor=self.actor_id,
                    action=item["action"],
                    rationale=item["rationale"]
                )
            )

        # --------------------------------------------------------
        # Return proposed Events only
        # No selection, probabilities, or history updates
        # --------------------------------------------------------

        return options

# ===============================================================================


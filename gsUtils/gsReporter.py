from gsLLM import callLLM


class PressReporter:

    def __init__(self, client, model, provider,
                 agent_id, generic_role, effort="medium"):

        self.client = client
        self.model = model
        self.provider = provider
        self.agent_id = agent_id
        self.generic_role = generic_role
        self.effort = effort

    def generate(self, W, E, report_prompt):
        """
        Generate a report from a completed GeoSim scenario.

        LOGIC
        -----
        1. Read all WorldStates and executed Events.
        2. Assemble them in chronological order:
             W0 > E0 > W1 > E1 > W2 > ...
        3. Supply the complete history to the LLM.
        4. Apply the selected reporting prompt.
        5. Return the generated report as text.

        Does not modify W or E.
        """

        if len(W) != len(E) + 1:
            raise ValueError("Inconsistent WorldState/Event histories")

        history = []

        for i, state in enumerate(W):
            history.append(state.to_json())

            if i < len(E):
                history.append(E[i].to_json())

        system_prompt = (
            f"Reporter identity: {self.agent_id}\n\n"
            + self.generic_role
        )

        user_prompt = (
            report_prompt
            + "\n\nCOMPLETE SCENARIO HISTORY\n\n"
            + "\n\n".join(history)
        )

        return callLLM(
            self.client,
            system_prompt,
            user_prompt,
            model=self.model,
            provider=self.provider,
            effort=self.effort
        )
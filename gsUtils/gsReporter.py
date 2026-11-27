# ================================================================
#  GeoSim | युगनीति · यन्त्रदर्पण
#  Computational Exploration of Strategic Futures
# ----------------------------------------------------------------
#  Designed and developed by Prithwis Mukerjee, PhD
#  Copyright © 2026 Prithwis Mukerjee
#
#  Exploring possible futures, not predicting a predetermined one.
# ================================================================
from gsLLM import callLLM
import json
from dataclasses import asdict

class PressReporter:

    def __init__(self, client, model, provider,
                 agent_id, generic_role, effort="medium"):

        self.client = client
        self.model = model
        self.provider = provider
        self.agent_id = agent_id
        self.generic_role = generic_role
        self.effort = effort

    def generate(self, W, E, report_prompt, A=None):
        """
        Generate a report from a completed GeoSim scenario.

        W : WorldState history
        E : Executed Event history
        A : Strategic Alternatives history (optional)

        Does not modify W, E or A.
        """

        if len(W) != len(E) + 1:
            raise ValueError("Inconsistent WorldState/Event histories")

        history = []

        for i, state in enumerate(W):
            history.append(state.to_json())

            if i < len(E):
                history.append(json.dumps(asdict(E[i]), indent=2))

        system_prompt = (
            f"Reporter identity: {self.agent_id}\n\n"
            + self.generic_role
        )

        user_prompt = (
            report_prompt
            + "\n\nCOMPLETE SCENARIO HISTORY\n\n"
            + "\n\n".join(history)
        )

        # Include Strategic Alternatives if supplied
        if A is not None:
            user_prompt += (
                "\n\nSTRATEGIC ALTERNATIVES HISTORY\n\n"
                + json.dumps([asdict(a) for a in A], indent=2)
            )

        return callLLM(
            self.client,
            system_prompt,
            user_prompt,
            model=self.model,
            provider=self.provider,
            effort=self.effort,
            agent_id=self.agent_id
        )
# ============================================================
# gsBookMaker.py
# GeoSim - BookMaker probability assessments
# ============================================================

import json
import math

from gsLLM import callLLM


class BookMaker:
    """Assess an Actor's options from one fixed analytical perspective.

    The generic role, specific role and evaluation prompt are fixed for
    this instance. Each evaluate() call uses the latest W and E entries.
    It returns independent assessments; it does not modify Events.
    """

    def __init__(self, client, model, provider,
                 generic_role, role, evaluate_prompt,
                 effort="medium"):

        self.client = client
        self.model = model
        self.provider = provider
        self.effort = effort

        self.generic_role = generic_role
        self.role = role
        self.evaluate_prompt = evaluate_prompt

    def _event_to_text(self, event):
        return f"""
Event ID  : {event.event_id}
Actor     : {event.actor}
Action    : {event.action}
Rationale : {event.rationale}
""".strip()

    def _world_to_text(self, world):
        """Present the same compact state context used by Actor.propose()."""
        lines = [f"WorldState: {world.state_id}", ""]

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

    def evaluate(self, W, E, options, actor):
        """Return one probability and rationale per proposed Event.

        Output: list[dict] with option_index, probability and rationale.
        No selection, Event mutation, or history updates take place.
        """
        if not W or not E or not options:
            raise ValueError("W, E and options must be non-empty")

        if any(option.actor != actor.actor_id for option in options):
            raise ValueError("All proposed Events must belong to the responding Actor")

        # Temporary diagnostics
        #print("WorldState :", W[-1].state_id)
        #print("Last Event :", E[-1].event_id)


        # Generic and specific BookMaker perspectives are fixed for this run.
        system_prompt = f"""
GENERIC BOOKMAKER ROLE
======================
{self.generic_role}

SPECIFIC BOOKMAKER ROLE
=======================
{self.role}
""".strip()

        # Number and order of options come from Actor.propose().
        option_text = "\n\n".join(
            f"OPTION {i}\n"
            f"Action    : {option.action}\n"
            f"Rationale : {option.rationale}"
            for i, option in enumerate(options)
        )

        user_prompt = f"""
LAST EVENT
==========
{self._event_to_text(E[-1])}

CURRENT WORLDSTATE
==================
{self._world_to_text(W[-1])}

RESPONDING ACTOR
================
Actor ID    : {actor.actor_id}
Name        : {actor.name}
Description : {actor.description}
Strategic role:
{actor.role}

PROPOSED EVENTS
===============
{option_text}

EVALUATION INSTRUCTIONS
=======================
{self.evaluate_prompt}
""".strip()

        response = callLLM(
            self.client,
            system_prompt,
            user_prompt,
            model=self.model,
            provider=self.provider,
            effort=self.effort
        )

        if isinstance(response, str):
            response = response.strip()
            if response.startswith("```"):
                response = response.split("\n", 1)[1]
                response = response.rsplit("```", 1)[0].strip()
            assessments = json.loads(response)
        else:
            assessments = response

        if not isinstance(assessments, list) or len(assessments) != len(options):
            raise ValueError("BookMaker must assess every option exactly once")

        for i, item in enumerate(assessments):
            if not isinstance(item, dict) or set(item) != {
                "option_index", "probability", "rationale"
            }:
                raise ValueError(f"Invalid BookMaker assessment at option {i}")
            if type(item["option_index"]) is not int or item["option_index"] != i:
                raise ValueError(f"Incorrect option index at position {i}")
            p = item["probability"]
            if type(p) not in (int, float) or not math.isfinite(p) or not 0 <= p <= 1:
                raise ValueError(f"Invalid probability at option {i}")
            if not isinstance(item["rationale"], str) or not item["rationale"].strip():
                raise ValueError(f"Missing rationale at option {i}")

        if not math.isclose(sum(item["probability"] for item in assessments),
                            1.0, rel_tol=0, abs_tol=0.001):
            raise ValueError("BookMaker probabilities must sum to 1")

        return assessments


# =============================================================================================
def initialiseBookMakers(client, model, provider,
                        BM_Generic, BM_Political_Role,
                        BM_Commercial_Role, BM_Prompt,
                        effort="medium"):

    BM_Political = BookMaker(
        client, model, provider,
        BM_Generic, BM_Political_Role, BM_Prompt,
        effort=effort
    )

    BM_Commercial = BookMaker(
        client, model, provider,
        BM_Generic, BM_Commercial_Role, BM_Prompt,
        effort=effort
    )

    return BM_Political, BM_Commercial
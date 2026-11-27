# ================================================================
#  GeoSim | युगनीति · यन्त्रदर्पण
#  Computational Exploration of Strategic Futures
# ----------------------------------------------------------------
#  Designed and developed by Prithwis Mukerjee, PhD
#  Copyright © 2026 Prithwis Mukerjee
#
#  Exploring possible futures, not predicting a predetermined one.
# ================================================================

import json
from datetime import datetime
from zoneinfo import ZoneInfo
import pytz
from pathlib import Path
from gsWorld import Event, WorldVariable, WorldState
from gsActors import Actor
from gsReporter import *
from gsWorld import *

# ====================================================================================

def getWorldFacts(MD_DIR):
    md_files = sorted(MD_DIR.glob("*.md"))

    if not md_files:
        raise FileNotFoundError(f"No Markdown files found in {MD_DIR}")

    world_facts = "\n\n".join(
        f"\n{'=' * 70}\n"
        f"SOURCE: {file.name}\n"
        f"{'=' * 70}\n\n"
        f"{file.read_text(encoding='utf-8')}"
        for file in md_files
    )

    print(f"Loaded {len(md_files)} WorldFacts files")
    print(f"Total characters: {len(world_facts):,}")
    return world_facts
    
# ====================================================================================

def getTriggerEvent(eventFile, n):
    with open(eventFile, encoding="utf-8") as f:
        data = json.load(f)

    TriggerEvents = [Event(**e) for e in data["events"]]

    # Choose either event
    #TriggerEvent = TriggerEvents[0]    # US export restrictions
    #TriggerEvent = TriggerEvents[1]    # Chinese lithography breakthrough
    return TriggerEvents[n]

    #TriggerEvent.show()
    

# ====================================================================================
    
def initialiseActors(actorFile, client, model, provider, effort="medium"):
    import json
    #from gsAgents import Actor

    with open(actorFile, "r", encoding="utf-8") as f:
        data = json.load(f)

    ActorsL = [
        Actor(
            client=client,
            model=model,
            provider=provider,
            effort=effort,
            **a
        )
        for a in data["actors"]
    ]

    ActorsD  = {a.actor_id: a for a in ActorsL}
    '''
    print("Actors initialised:", len(ActorsL))
    for actor in ActorsL:
        print(actor.actor_id, ":", actor.name)
    '''
    return ActorsL, ActorsD
    

# ====================================================================================



def nextActor(W, E, ActorL, ActorD,
              client, model, provider, NXTA_Role,
              effort="medium"):
    """
    Select the next Actor in GeoSim.

    LOGIC
    -----
    1. Validate simulation histories and participating Actors.
    2. Exclude the Actor responsible for the last Event.
    3. With two Actors, select the other Actor directly.
    4. With three or more Actors:
       - Supply the current WorldState.
       - Supply the latest executed Event.
       - Supply the complete executed Event history.
       - Supply eligible Actors and their strategic roles.
       - Apply the external NXTA_Role prompt.
    5. Let the LLM select the most appropriate respondent.
       The ROLE prompt governs strategic relevance and
       the five-epoch inactivity preference.
    6. Validate the returned Actor ID and rationale.
    7. Return the Actor object and selection rationale.

    Does not modify W, E, or Actor objects.
    """

    import json
    from dataclasses import asdict
    from gsLLM import callLLM

    if not E or len(W) != len(E) + 1:
        raise ValueError("Invalid WorldState/Event history")

    if len(ActorL) < 2:
        raise ValueError("At least two Actors are required")

    last_id = E[-1].actor

    if last_id not in ActorD:
        raise ValueError(f"Unknown previous Actor: {last_id}")

    # Exclude the Actor responsible for the last Event
    eligible = [
        actor for actor in ActorL
        if actor.actor_id != last_id
    ]

    if not eligible:
        raise ValueError("No eligible Actors")

    # Two-Actor case: deterministic selection
    if len(ActorL) == 2:
        actor = eligible[0]
        reason = (
            f"{actor.name} is the other participating Actor "
            "and is selected to respond."
        )
        return actor, reason

    # Three or more Actors: LLM selection

    candidates = [
        {
            "actor_id": actor.actor_id,
            "name": actor.name,
            "description": actor.description,
            "role": actor.role
        }
        for actor in eligible
    ]

    # Complete executed history, including E0
    history = [
        {
            "event_id": event.event_id,
            "actor": event.actor,
            "action": event.action
        }
        for event in E
    ]

    system_prompt = NXTA_Role

    user_prompt = f"""
CURRENT WORLDSTATE
==================
{W[-1].to_json()}

LATEST EXECUTED EVENT
=====================
{json.dumps(asdict(E[-1]), indent=2)}

EXECUTED EVENT HISTORY
======================
{json.dumps(history, indent=2)}

ELIGIBLE ACTORS
===============
{json.dumps(candidates, indent=2)}
""".strip()

    response = callLLM(
        client,
        system_prompt,
        user_prompt,
        model=model,
        provider=provider,
        effort=effort,
        agent_id="ActorSelector"
    )

    # Parse LLM response
    if isinstance(response, str):
        response = response.strip()

        if response.startswith("```"):
            response = response.split("\n", 1)[1]
            response = response.rsplit("```", 1)[0].strip()

        result = json.loads(response)
    else:
        result = response

    # Validate selection
    if not isinstance(result, dict) or set(result) != {
        "actor_id", "reason"
    }:
        raise ValueError("Invalid Actor Selector response")

    actor_id = result["actor_id"]
    reason = result["reason"]

    eligible_ids = {a.actor_id for a in eligible}

    if actor_id not in eligible_ids:
        raise ValueError(f"Ineligible Actor selected: {actor_id}")

    if not isinstance(reason, str) or not reason.strip():
        raise ValueError("Missing Actor selection rationale")

    return ActorD[actor_id], reason


# ====================================================================================

def snapShot(W, E, textVar=""):
    """Print a message and the latest simulation transition."""
    print(f"{textVar} : {W[-2].state_id} > {E[-1].event_id} > {W[-1].state_id}")

# ====================================================================================

# Probabilities

# ====================================================================================
def setOdds(options, P, C, actor_id, ActorWeights, alpha=None):
    """
    Determine the Political/Commercial weighting.

    If alpha is supplied, use it.
    Otherwise, obtain it from ActorWeights using actor_id.
    """

    if alpha is None:
        category = actor_id.split("_", 1)[0]
        alpha = ActorWeights[category] / 100

    # Existing validation and probability synthesis follows
    """
    Combine Political and Commercial BookMaker probabilities.

    LOGIC
    -----
    1. Receive the proposed Events and two BookMaker assessments.
    2. Validate alpha, where:
           alpha     = Political BookMaker weight
           1 - alpha = Commercial BookMaker weight
    3. Validate that both BookMakers have assessed every option.
    4. Extract probabilities using option_index.
    5. Verify that each probability distribution sums to 1.
    6. Calculate the weighted probability for each option:

           Final = alpha * Political + (1-alpha) * Commercial

    7. Normalize the final probabilities.
    8. Assign selection_weight to each proposed Event.
    9. Return the updated list of options.

    No Event is selected or added to Event history.
    """

    import math

    if not 0 <= alpha <= 1:
        raise ValueError("alpha must be between 0 and 1")

    n = len(options)
    if n == 0:
        raise ValueError("No Event options supplied")

    # Extract and validate BookMaker probabilities
    def getProbabilities(results, name):

        if len(results) != n:
            raise ValueError(f"{name}: incorrect option count")

        probabilities = {}

        for item in results:
            i = item["option_index"]
            p = item["probability"]

            if type(i) is not int or i not in range(n):
                raise ValueError(f"{name}: invalid option_index")

            if i in probabilities:
                raise ValueError(f"{name}: duplicate option_index")

            if not isinstance(p, (int, float)) or \
               not math.isfinite(p) or not 0 <= p <= 1:
                raise ValueError(f"{name}: invalid probability")

            probabilities[i] = p

        if not math.isclose(
            sum(probabilities.values()), 1.0, abs_tol=1e-6
        ):
            raise ValueError(f"{name}: probabilities do not sum to 1")

        return [probabilities[i] for i in range(n)]

    political = getProbabilities(P, "Political BM")
    commercial = getProbabilities(C, "Commercial BM")

    # Weighted probability synthesis
    weights = [
        alpha * political[i] + (1 - alpha) * commercial[i]
        for i in range(n)
    ]

    # Normalize and assign selection weights
    total = sum(weights)

    for option, weight in zip(options, weights):
        option.selection_weight = weight / total

    return options

# ====================================================================================


def rollDice(options, E):
    """
    Select one Event using weighted random sampling.

    LOGIC
    -----
    1. Read the selection_weight of each proposed Event.
    2. Validate that the weights are non-negative and sum to 1.
    3. Randomly select one Event using those weights.
    4. Assign the next Event ID using the current history length.
       For example, if E contains E0, assign E1.
    5. Return the selected Event.

    Does not append the Event to E or modify WorldState.
    """
    import random
    import math

    if not options:
        raise ValueError("No Event options supplied")

    weights = [option.selection_weight for option in options]

    if any(
        not isinstance(w, (int, float)) or
        not math.isfinite(w) or w < 0
        for w in weights
    ):
        raise ValueError("Invalid selection weights")

    if not math.isclose(sum(weights), 1.0, abs_tol=1e-6):
        raise ValueError("Selection weights must sum to 1")

    selected = random.choices(
        options,
        weights=weights,
        k=1
    )[0]

    selected.event_id = f"E{len(E)}"

    return selected

# ====================================================================================

def recAlternatives(options, P, C, selected,
                    actor_id, ActorWeights):

    from copy import deepcopy

    category = actor_id.split("_", 1)[0]
    alpha = ActorWeights[category] / 100

    selected_index = next(
        i for i, option in enumerate(options)
        if option is selected
    )

    return Alternatives(
        options=deepcopy(options),
        P=deepcopy(P),
        C=deepcopy(C),
        alpha=alpha,
        selected_index=selected_index
    )
# ====================================================================================
def generateReports(W, E, A, PR_Narrative, PR_Structured,
                    PR_PathNotTaken, Reporter):

    # Generate reports
    NarrativeReport = Reporter.generate(W, E, PR_Narrative)
    #StructuredReport = Reporter.generate(W, E, PR_Structured)
    PathNotTakenReport = Reporter.generate(W, E, PR_PathNotTaken, A=A)

    # Unique identifier for this scenario run
    runID = datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%y%m%d_%H%M%S")

    # Define report filenames
    narrativeFile = Path(f"/content/GeoSim_{runID}_Narrative.txt")
    #structuredFile = Path(f"/content/GeoSim_{runID}_Structured.md")
    pathNotTakenFile = Path(f"/content/GeoSim_{runID}_PathNotTaken.txt")

    # Save reports
    narrativeFile.write_text(NarrativeReport, encoding="utf-8")
    #structuredFile.write_text(StructuredReport, encoding="utf-8")
    pathNotTakenFile.write_text(PathNotTakenReport, encoding="utf-8")

    print("Narrative Report :", narrativeFile)
    #print("Structured Report:", structuredFile)
    print("Path Not Taken   :", pathNotTakenFile)

    return NarrativeReport, PathNotTakenReport

# ====================================================================================
def auditTrail(A, filename="auditTrail.txt"):
    """
    Generate a complete audit trail of strategic alternatives
    after all simulation epochs have been completed.
    """

    lines = [
        "# GeoSim — Strategic Alternatives Audit Trail",
        "",
        f"Total Epochs: {len(A)}",
        ""
    ]

    for epoch, a in enumerate(A, start=1):

        selected = a.options[a.selected_index]

        lines.extend([
            "---",
            "",
            f"## Epoch {epoch}",
            "",
            f"**Actor:** {selected.actor}",
            "",
            f"**Actor Selection Rationale:** "
            f"{selected.actor_selection_rationale}",
            "",
            f"**Political Weight (Alpha):** {a.alpha:.2f}",
            "",
            f"**Selected Event:** {selected.event_id}",
            "",
            "### Probability Summary",
            "",
            "| Alternative | Political | Commercial | Combined | Status |",
            "|---|---:|---:|---:|---|"
        ])

        for i, option in enumerate(a.options):

            status = (
                "**SELECTED**" if i == a.selected_index
                else "Not Selected"
            )

            lines.append(
                f"| {i+1} | "
                f"{a.P[i]['probability']:.2%} | "
                f"{a.C[i]['probability']:.2%} | "
                f"{option.selection_weight:.2%} | "
                f"{status} |"
            )

        lines.append("")

        for i, option in enumerate(a.options):

            status = (
                "SELECTED" if i == a.selected_index
                else "NOT SELECTED"
            )

            lines.extend([
                f"### Alternative {i+1} — {status}",
                "",
                "**Proposed Action**",
                "",
                option.action,
                "",
                "**Strategic Rationale**",
                "",
                option.rationale,
                "",
                "**Political BookMaker Rationale**",
                "",
                a.P[i]["rationale"],
                "",
                "**Commercial BookMaker Rationale**",
                "",
                a.C[i]["rationale"],
                ""
            ])

    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Audit Trail saved to {filename}")

# ====================================================================================

def resetScenario(W, E, A):
    """Reset simulation to W0 > E0 > W1."""
    del W[2:]
    del E[1:]
    A = []


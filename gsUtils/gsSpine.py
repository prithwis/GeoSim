import json
from gsWorld import Event, WorldVariable, WorldState
from gsActors import Actor

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

def nextActor(E, ActorL, ActorD):

    last_id = E[-1].actor
    last_index = ActorL.index(ActorD[last_id])
    next_index = (last_index + 1) % len(ActorL)

    return ActorL[next_index]

# ====================================================================================

def snapShot(W, E, textVar=""):
    """Print a message and the latest simulation transition."""
    print(f"{textVar} : {W[-2].state_id} > {E[-1].event_id} > {W[-1].state_id}")

# ====================================================================================

# Probabilities

# ====================================================================================
def setOdds(options, P, C, alpha=0.6):
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
    
def resetScenario(W, E):
    """Reset simulation to W0 > E0 > W1."""
    del W[2:]
    del E[1:]


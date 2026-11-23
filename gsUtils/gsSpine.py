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
    #TriggerEvent = TriggerEvents[0]   # US export restrictions
    #TriggerEvent = TriggerEvents[1] # Chinese lithography breakthrough
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

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
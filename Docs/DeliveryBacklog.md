# Delivery backlog

2026-10-24. Local coordination record. The complete original campaign is the destination; current work includes preproduction, a technical foundation and a campaign sprite candidate library. No public tracker, PR or external message was created.

| Owner / model | Current work | State | Next action |
|---|---|---|---|
| Coordinator | References, enemy and effect art, integration, review | Style approved; 128 enemy source candidates and expanded effect library produced | Review campaign gallery and close map/event asset gaps |
| GPT-6.1 core agent | Content packs, sample combat/progression, keywords, saves, Unity adapter | Behavioral and installed-API checks; see CoreValidation.md | Activate Unity license, import project, validate and playtest sandbox |
| GPT-6.1 interface agent | Eight wireframes and interactive review board | 21 source/interaction checks passed; exported contact sheet inspected | Review original-screen layout differences; verify in a real browser |
| GPT-6.1 party agent | Party poses, icons and special effects | Nine playable party sets and supplemental sheets exported as candidates | Polish motion and compare original costumes and silhouettes |
| GPT-6.1 pipeline agent | Export, provenance, coverage and review gallery | Manifest-driven native exports and independent reconstruction checks | Run licensed Unity import validation after native review |
| GPT-6 Luna world agent | NPC movement, transport, equipment, props and effects | Twenty NPC identities plus world sheets; independent contact-sheet QA recorded | Strengthen subtle robe/rear walk motion and transport orientation cues |
| GPT-6 Luna review agent | Save/content correctness review | Findings routed to core agent | Confirm scoped fixes and retain unresolved limitations in architecture |

## Ordered milestones

1. **Visual agreement.** Review all three art sheets and eight interfaces. Lock canvas/pixel aspect, sprite footprint, palette and original-screen composition from measured captures. Export a small native-pixel sprite/tileset proof; current generated boards are not production atlases.
2. **Playable original opening segment.** Implement original-style party-command collection/resolution, collision and transitions, authored dialogue/keyword events, inventory/equipment and magic, original save eligibility/four slots, sound and sprite animation. Reconstruct opening events through an agreed early-game checkpoint using audited source layouts. Acceptance: play from New Game to checkpoint, save/reload and continue without debug actions.
3. **Campaign content ledger.** Enumerate the entire story graph, maps/doors, NPC states, encounters, treasure, recruit/departure events, vehicles, spells, enemies and bosses. Each record needs a stable ID, source evidence, dependencies and a verification case. Unknown counts remain unknown until reconciled.
4. **Complete campaign implementation.** Produce successive story/location groups in dependency order, covering every main-story route through the ending. Audit world-state transitions and revisitable areas; avoid designing content from memory. Acceptance includes continued saves across content updates and no progression blockers.
5. **Expansion proof.** Use a separate sample pack with one optional map, NPC/event chain, encounter and reward. It must be addable without editing base campaign definitions, preserve existing saves, and clearly explain behavior when required content is absent. The current demo pack proves catalog boundaries only, not a complete expansion-authoring workflow.
6. **Release candidate verification.** Native-resolution comparisons, complete-campaign playthrough, progression/balance reference checks, keyboard/controller flows, localization overflow, audio timing, save migration/recovery, build and performance checks. Record exact source revision and build artifacts. Publication remains a separate explicitly authorized action.

## Working contracts

- GPT-6.1 owns architecture, hard integration and fidelity decisions. Luna receives bounded data/art-preparation tasks with explicit examples and acceptance criteria.
- Assign non-overlapping files or isolated worktrees once the repository has commits. Preserve current work and generated artifacts. Authors do not approve their own fidelity changes without review.
- Keep a task's implementation evidence distinct from concept approval, Unity compilation, runtime tests, playable builds and complete content coverage.
- New mechanics are explicit core rules behind presentation boundaries. New content reuses stable IDs and declared dependencies. Never represent a generic `quest` or `spell` record as a functioning quest or magic system.
- Art approval gates scaling production; it does not require asking Constantine to approve every routine code change or asset entry.

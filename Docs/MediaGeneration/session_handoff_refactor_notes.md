# FAL Video Pipeline Session Handoff

## Current Goal

Build a frictionless FAL video generation workflow where the user can give a simple thought, Codex expands it into a managed project, then walks through gated generation:

```text
thought -> brief -> scene plan -> storyboard stills -> image-to-video clips -> voiceover -> review cut
```

The UI is useful as a first pass, but the stronger near-term direction is the `fal-video-pipeline` Codex skill.

## Working Proofs

### Smart Websites For Small Companies

Generated end to end:

- storyboard stills
- image-to-video clips
- review cut
- FAL TTS voiceover
- final voiceover mix

Final:

```text
Docs/MediaGeneration/outputs/review/smart_websites_for_small_companies_with_fal_voiceover.mp4
```

### Tiny Robot Baker

Generated end to end:

- project from one thought
- animated story scene plan
- storyboard stills
- image-to-video clips
- review cut
- FAL TTS voiceover
- final voiceover mix

Final:

```text
Docs/MediaGeneration/outputs/review/tiny_robot_baker_with_fal_voiceover.mp4
```

Manifest:

```text
Docs/MediaGeneration/manifests/tiny_robot_baker_manifest.json
```

## Important Convention Change

Future generated assets should be saved into project-specific folders:

```text
Docs/MediaGeneration/outputs/text_to_image/<project>/
Docs/MediaGeneration/outputs/image_to_video/<project>/
Docs/MediaGeneration/outputs/text_to_speech/<project>/
Docs/MediaGeneration/outputs/review/<project>/
```

The FAL runner now supports:

```powershell
--project PROJECT_NAME
```

Example:

```powershell
.\run_fal.bat --model fal-ai/flux/schnell --args Docs\MediaGeneration\recipes\text_to_image\tiny_robot_baker_scene_001.json --out Docs\MediaGeneration\outputs\text_to_image --project tiny_robot_baker
```

Existing older outputs were not moved, to avoid breaking manifests.

## Code Added Or Changed

### FAL Runner

```text
Python/scripts/media/fal_generate.py
```

Important additions:

- `--upload-file key=path`
- `--project PROJECT_NAME`
- project-specific output subfolders

### Local Studio UI

```text
Python/scripts/studio/server.py
web/studio/index.html
web/studio/app.js
web/studio/styles.css
run_studio.bat
```

UI status:

- Has SQLite project/job registry.
- Has project type catalog.
- Has one-thought project creation.
- Raw manual job launcher was removed after it caused repeated real FAL calls.
- UI is not the priority right now; refactor later.

SQLite:

```text
Docs/MediaGeneration/studio.sqlite3
```

### Codex Skill

```text
C:\Users\user\.codex\skills\fal-video-pipeline
```

Key files:

```text
SKILL.md
references/checklists.md
agents/openai.yaml
scripts/write_checklist.py
```

The skill has been refocused around:

```text
simple thought -> minimal questions -> plan -> storyboard -> animate -> voiceover -> review cut
```

Validated with:

```text
Skill is valid!
```

## Refactor Targets

1. Make project-specific output folders the only path everywhere.
2. Update manifest-writing helpers so they do not require manual patching.
3. Add a deterministic project creator script:

```text
scripts/create_video_project.py
```

Inputs:

```text
thought
project_type
duration
aspect_ratio
voiceover
```

Outputs:

```text
brief
scene_plan
recipes
manifest
```

4. Add stage scripts:

```text
generate_storyboards.py
generate_clips.py
generate_voiceover.py
assemble_review.py
```

5. Keep paid stages gated:

```text
storyboard approval
clip approval
voiceover approval
assembly approval
```

6. Consider moving old generated assets into project folders only after updating manifests.

## Known Gotchas

- FAL TTS often returns audio longer than a 20-second cut. We tempo-matched for review, but final polish should either shorten the script or extend the edit.
- FAL video outputs may not honor requested 16:9 exactly. We padded/re-encoded review cuts to 1920x1080.
- Generated readable text is unreliable. Add exact text in edit layer.
- Do not bring back a raw browser "Start Job" form that defaults to a real FAL command.

## Good Future Prompt

```text
Use fal-video-pipeline. Make a 20 second animated story about a tiny robot baker learning teamwork.
```

Expected behavior:

1. Ask only missing questions.
2. Create project files.
3. Show scene plan.
4. Ask before paid storyboards.
5. Ask before image-to-video.
6. Ask before TTS.
7. Assemble and verify final review cut.

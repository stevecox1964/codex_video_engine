# Codex Video Engine

Codex Video Engine is an experimental FAL-powered video generation workspace. The target workflow is:

```text
thought -> brief -> scene plan -> storyboard stills -> image-to-video clips -> voiceover -> review cut
```

The repo currently contains the working proof assets as docs, recipes, manifests, a general FAL runner, and a first-pass local studio UI. Generated media outputs are intentionally ignored by git.

## Project Structure

```text
.
+-- Docs/
|   +-- MediaGeneration/
|       +-- assets/
|       |   +-- references/          # Reference assets for future projects
|       +-- briefs/                  # Project briefs generated from video ideas
|       +-- manifests/               # Generation manifests and project state
|       +-- outputs/                 # Local generated media, ignored except .gitkeep
|       |   +-- image_to_video/
|       |   +-- review/
|       |   +-- text_to_image/
|       |   +-- text_to_speech/
|       |   +-- text_to_video/
|       +-- recipes/                 # FAL request JSON by generation mode
|       |   +-- image_to_video/
|       |   +-- storyboards/
|       |   +-- text_to_image/
|       |   +-- text_to_speech/
|       |   +-- text_to_video/
|       +-- storyboards/             # Scene plans
|       +-- templates/               # Starter manifest, brief, and scene templates
|       +-- fal_video_generation_workflow.md
|       +-- generation_types.md
|       +-- jay_style_fal_pipeline.md
|       +-- session_handoff_refactor_notes.md
+-- Python/
|   +-- scripts/
|       +-- media/
|       |   +-- fal_generate.py      # General FAL runner
|       |   +-- fal_kandinsky_smoke.py
|       |   +-- fetch_fal_result.py
|       +-- studio/
|           +-- server.py            # FastAPI local studio backend
+-- web/
|   +-- studio/                      # Local studio frontend
+-- fetch_text_to_video_result.bat
+-- run_fal.bat
+-- run_studio.bat
+-- run_text_to_video_now.bat
+-- test_fal_key.bat
+-- pyproject.toml
+-- uv.lock
```

## Setup

Install dependencies with `uv`:

```powershell
uv sync
```

Create a local `.env` file with your FAL key:

```text
FAL_KEY=your_fal_key_here
```

`.env` is ignored by git.

To verify authentication:

```powershell
.\test_fal_key.bat
```

## Running The FAL Runner

Use `run_fal.bat` with a model, recipe JSON, output folder, and project name:

```powershell
.\run_fal.bat --model fal-ai/flux/schnell --args Docs\MediaGeneration\recipes\text_to_image\tiny_robot_baker_scene_001.json --out Docs\MediaGeneration\outputs\text_to_image --project tiny_robot_baker
```

For image-to-video jobs that need a local still uploaded first:

```powershell
.\run_fal.bat --model fal-ai/kling-video/v3/standard/image-to-video --args Docs\MediaGeneration\recipes\image_to_video\tiny_robot_baker_scene_001.json --upload-file start_image_url=Docs\MediaGeneration\outputs\text_to_image\tiny_robot_baker\scene_001.jpg --out Docs\MediaGeneration\outputs\image_to_video --project tiny_robot_baker
```

Generated assets should use project-specific folders:

```text
Docs/MediaGeneration/outputs/text_to_image/<project>/
Docs/MediaGeneration/outputs/image_to_video/<project>/
Docs/MediaGeneration/outputs/text_to_speech/<project>/
Docs/MediaGeneration/outputs/review/<project>/
```

## Running The Studio

Start the local studio:

```powershell
.\run_studio.bat
```

The studio has a SQLite project/job registry and a first-pass one-thought project flow. The raw manual job launcher was removed to avoid accidental paid FAL calls.

## Current Proofs

Two end-to-end proofs were generated locally:

- Smart Websites For Small Companies
- Tiny Robot Baker

Their briefs, scene plans, recipes, and manifests are tracked in git. The generated MP4, JPG, MP3, and FAL result JSON files are local-only under `Docs/MediaGeneration/outputs/`.

## Next Refactor Targets

1. Make project-specific output folders the only path everywhere.
2. Add manifest-writing helpers so FAL results do not require manual patching.
3. Add `scripts/create_video_project.py` to create briefs, scene plans, recipes, and manifests from a simple thought.
4. Add stage scripts: `generate_storyboards.py`, `generate_clips.py`, `generate_voiceover.py`, and `assemble_review.py`.
5. Keep paid stages gated: storyboard approval, clip approval, voiceover approval, and assembly approval.

See `Docs/MediaGeneration/session_handoff_refactor_notes.md` for the current handoff notes.

# Jay-Style FAL Pipeline

This is the practical translation of the saved Jay-style workflows into this repo.

## What We Are Building

A local FAL production system where Codex can:

1. Take a concept, script, URL, logo, or reference image.
2. Create a scene plan and storyboard.
3. Ask for approval before paid generation.
4. Generate still frames first when control matters.
5. Generate short video clips from approved prompts or images.
6. Save all outputs locally.
7. Build a review manifest for editing.

## Roles

```text
User: director
Codex: operator
FAL: model access layer
FFmpeg/Remotion/Hyperframes: edit/render layer
```

## Workflow A: Quick Video Smoke Test

Use this only to verify that video generation works.

```powershell
.\test_text_to_video.bat
```

## Workflow B: Promo Clip

Use this for an app, website, product, plugin, or service.

1. Create a brief in `Docs/MediaGeneration/briefs/`.
2. Create a scene plan in `Docs/MediaGeneration/storyboards/`.
3. Generate still frames with text-to-image.
4. Review and approve the stills.
5. Generate image-to-video clips.
6. Save a manifest in `Docs/MediaGeneration/manifests/`.
7. Assemble with an edit/render tool.

## Workflow C: Long Video

Use this for faceless videos, explainers, and story videos.

1. Start from a script or voiceover transcript.
2. Split into 3 to 5 second scenes.
3. Write one prompt per scene.
4. Generate storyboard stills.
5. Approve the storyboard.
6. Generate video clips scene by scene.
7. Track every clip in a manifest.

## Workflow D: Logo Animation

Use this for a 4 to 6 second brand reveal.

1. Put the logo/reference image in `Docs/MediaGeneration/assets/references/`.
2. Create a 4 to 6 panel motion plan.
3. Generate or select the best keyframe.
4. Send the keyframe to image-to-video.
5. Add exact logo/text treatment later in the edit layer if needed.

## Quality Rules

- Prefer image-to-video when consistency matters.
- Treat generated text as unreliable unless it is large and simple.
- Keep model prompts cinematic but concrete: subject, camera, motion, lighting, background, exclusions.
- Record every generation in a manifest so good outputs are reproducible.
- Escalate cost only after a low-cost proof works.

# FAL Video Generation Workflow

This project uses fal.ai as the model API layer and Codex as the production operator.

The working pattern comes from the saved Jay E / RoboNuggets video workflows:

- Use an agent to write prompts, call models, poll jobs, and collect outputs.
- Keep the human in the director role: approve plans, storyboards, cost, and final takes.
- Generate stills or storyboards before spending more on video.
- For longer videos, split the concept into short scenes and batch the boring work.
- Use a local edit layer such as FFmpeg, Remotion, or Hyperframes after model generation.

## Production Loop

```text
brief
-> scene plan
-> storyboard or still frames
-> director approval
-> paid FAL generation
-> downloaded clips
-> review manifest
-> edit/render layer
```

## Local Folder Shape

```text
Docs/MediaGeneration/
  briefs/
  templates/
  storyboards/
  manifests/
  assets/
    references/
  recipes/
    text_to_image/
    text_to_video/
    image_to_video/
    storyboards/
  outputs/
    text_to_image/
    text_to_video/
    image_to_video/
    review/
```

## Approval Contract

Before any paid generation, Codex should show:

```text
Model:
Mode:
Count:
Aspect ratio:
Duration:
Resolution:
Inputs:
Estimated cost/risk:
Output folder:
Proceed?
```

## Generation Modes

### Text to Video

Use for the first smoke test or simple concept clips.

```powershell
.\test_text_to_video.bat
```

Direct command:

```powershell
.\run_fal.bat --model fal-ai/kandinsky5/text-to-video/distill --args Docs\MediaGeneration\recipes\text_to_video\kandinsky5_smoke_test.json --out Docs\MediaGeneration\outputs\text_to_video
```

### Text to Image

Use for storyboard frames, concept art, product shots, and style exploration before video.

Planned command shape:

```powershell
.\run_fal.bat --model fal-ai/flux/schnell --args Docs\MediaGeneration\recipes\text_to_image\scene_001.json --out Docs\MediaGeneration\outputs\text_to_image
```

### Image to Video

Use after a still frame is approved. This is the preferred route for controlled motion, logo reveals, app promos, and consistent characters.

Planned command shape:

```powershell
.\run_fal.bat --model MODEL_ID --args Docs\MediaGeneration\recipes\image_to_video\scene_001.json --out Docs\MediaGeneration\outputs\image_to_video
```

## Jay-Style Defaults

- Default scene length: 3 to 5 seconds.
- Start cheap: one variant, low/standard resolution, short duration.
- Ask for approval after the scene plan and again after still frames.
- Do not try to force tiny readable text inside generated video. Put exact text in the edit layer.
- For app/product videos, use screenshots or reference images whenever possible.
- For long videos, generate a manifest and process one scene at a time.

## Source Videos Used

- Jay E / RoboNuggets: generative model connector workflow.
- Jay E / RoboNuggets: promotional video agent workflow.
- Jay E / RoboNuggets: Hyperframes V2 editing workflow.
- The Zinny Studio: long AI video workflow with scene splitting and approval gates.

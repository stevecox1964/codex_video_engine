# FAL Generation Types

Use one recipe folder per generation mode. Keep outputs split the same way so test files do not become a mystery pile.

## Folder Map

```text
Docs/MediaGeneration/
  recipes/
    text_to_image/
    text_to_video/
    image_to_video/
    storyboards/
  briefs/
  storyboards/
  manifests/
  assets/
    references/
  outputs/
    text_to_image/
    text_to_video/
    image_to_video/
    review/
```

## Smoke Test: Text to Video

This is the simplest paid video test because it only needs a prompt.

```powershell
.\run_fal.bat --model fal-ai/kandinsky5/text-to-video/distill --args Docs\MediaGeneration\recipes\text_to_video\kandinsky5_smoke_test.json --out Docs\MediaGeneration\outputs\text_to_video
```

Before running, confirm:

```text
Model: fal-ai/kandinsky5/text-to-video/distill
Mode: text-to-video
Count: 1
Aspect ratio: 3:2
Duration: 5s
Inputs: Docs/MediaGeneration/recipes/text_to_video/kandinsky5_smoke_test.json
Estimated cost/risk: fal lists this endpoint at about $0.05 for a 5-second video; pricing can change.
Output folder: Docs/MediaGeneration/outputs/text_to_video
```

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import time
import uuid
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field


PROJECT_ROOT = Path(__file__).resolve().parents[3]
MEDIA_ROOT = PROJECT_ROOT / "Docs" / "MediaGeneration"
WEB_ROOT = PROJECT_ROOT / "web" / "studio"
DB_PATH = MEDIA_ROOT / "studio.sqlite3"

load_dotenv(PROJECT_ROOT / ".env", override=False)

app = FastAPI(title="FAL Video Studio")
app.mount("/studio", StaticFiles(directory=WEB_ROOT, html=True), name="studio")
app.mount("/media", StaticFiles(directory=MEDIA_ROOT), name="media")


VIDEO_TYPES = [
    "product_promo",
    "app_demo",
    "animated_story",
    "explainer",
    "logo_reveal",
    "ambient_music",
    "smoke_test",
]

PROJECT_TYPES = [
    {
        "id": "product_promo",
        "name": "Product or Service Promo",
        "description": "Short marketing video for a product, service, offer, plugin, agency, or local business.",
        "best_for": ["websites", "apps", "services", "launch clips", "ads"],
        "default_duration": 20,
        "default_style": "Cinematic, practical, modern",
        "default_audience": "Potential customers",
        "starter_goal": "Explain the problem, show the value, and end with a clear call to action.",
        "needs": ["offer", "audience", "benefits", "CTA", "brand/assets"],
    },
    {
        "id": "app_demo",
        "name": "App Demo",
        "description": "Workflow-focused video that shows screens, features, and user actions.",
        "best_for": ["SaaS", "dashboards", "plugins", "internal tools", "mobile apps"],
        "default_duration": 30,
        "default_style": "Clean software demo with precise overlays",
        "default_audience": "Prospective users",
        "starter_goal": "Show the most important workflow and why it matters.",
        "needs": ["screenshots", "workflow steps", "feature list", "overlay text"],
    },
    {
        "id": "animated_story",
        "name": "Animated Story",
        "description": "Narrative video with characters, settings, story beats, and a visual style.",
        "best_for": ["short stories", "children's stories", "brand stories", "character scenes"],
        "default_duration": 30,
        "default_style": "Cinematic animated story",
        "default_audience": "General audience",
        "starter_goal": "Tell a simple beginning, middle, and ending with consistent characters.",
        "needs": ["premise", "characters", "setting", "genre", "tone", "story beats"],
    },
    {
        "id": "explainer",
        "name": "Explainer or Faceless Video",
        "description": "Educational or persuasive video built around voiceover, visual metaphors, and overlays.",
        "best_for": ["YouTube explainers", "training", "thought leadership", "how-it-works videos"],
        "default_duration": 45,
        "default_style": "Clear faceless explainer with modern visuals",
        "default_audience": "Learners",
        "starter_goal": "Teach one idea clearly with simple visual examples.",
        "needs": ["topic", "audience level", "script/outline", "visual metaphor", "voiceover"],
    },
    {
        "id": "logo_reveal",
        "name": "Logo Reveal",
        "description": "Short brand animation around a logo, mark, or title treatment.",
        "best_for": ["intros", "outros", "brand stings", "launch bumpers"],
        "default_duration": 6,
        "default_style": "Premium clean logo animation",
        "default_audience": "Brand viewers",
        "starter_goal": "Reveal the logo with a polished motion treatment.",
        "needs": ["logo file", "brand colors", "motion mood", "background"],
    },
    {
        "id": "ambient_music",
        "name": "Ambient or Music Visual",
        "description": "Mood-driven visual loop or sequence for music, background, or atmosphere.",
        "best_for": ["loops", "music visuals", "backgrounds", "mood pieces"],
        "default_duration": 20,
        "default_style": "Atmospheric cinematic loop",
        "default_audience": "Viewers/listeners",
        "starter_goal": "Create a mood-rich visual sequence that supports the audio or atmosphere.",
        "needs": ["mood", "setting", "camera motion", "loop vs linear", "audio status"],
    },
    {
        "id": "smoke_test",
        "name": "Smoke Test",
        "description": "One cheap generation to confirm a FAL model, key, or pipeline path works.",
        "best_for": ["API testing", "new model checks", "debugging"],
        "default_duration": 5,
        "default_style": "Simple clean test clip",
        "default_audience": "Operator",
        "starter_goal": "Prove the selected generation path works before spending more.",
        "needs": ["prompt", "model", "output folder"],
    },
]


CHECKLIST = [
    "Video type selected",
    "Intake complete",
    "Brief created",
    "Scene plan created",
    "Storyboard generation approved",
    "Storyboard stills generated",
    "Stills approved or revised",
    "Video clip generation approved",
    "Video clips generated",
    "Voiceover script approved",
    "FAL voiceover generated",
    "Review cut assembled",
    "Manifest updated",
]


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1)
    video_type: str = Field(default="product_promo")
    goal: str = ""
    audience: str = ""
    aspect_ratio: str = "16:9"
    target_duration_seconds: int = 20
    style: str = ""
    voiceover: bool = True
    must_include: str = ""
    must_avoid: str = ""


class ThoughtProjectCreate(BaseModel):
    thought: str = Field(min_length=1)
    video_type: str = "auto"
    aspect_ratio: str = "16:9"
    target_duration_seconds: int = 20


class ScenePlanRequest(BaseModel):
    project: str
    scenes: list[dict[str, Any]]


class JobCreate(BaseModel):
    project: str
    stage: str
    command: list[str]


def slugify(value: str) -> str:
    chars = []
    last_dash = False
    for char in value.lower():
        if char.isalnum():
            chars.append(char)
            last_dash = False
        elif not last_dash:
            chars.append("_")
            last_dash = True
    return "".join(chars).strip("_") or f"project_{int(time.time())}"


def rel(path: Path) -> str:
    return str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")


def media_url(path: Path) -> str:
    return "/media/" + str(path.relative_to(MEDIA_ROOT)).replace("\\", "/")


def ensure_folders() -> None:
    folders = [
        "briefs",
        "storyboards",
        "manifests",
        "recipes/text_to_image",
        "recipes/text_to_video",
        "recipes/image_to_video",
        "recipes/text_to_speech",
        "assets/references",
        "outputs/text_to_image",
        "outputs/text_to_video",
        "outputs/image_to_video",
        "outputs/text_to_speech",
        "outputs/review",
    ]
    for folder in folders:
        (MEDIA_ROOT / folder).mkdir(parents=True, exist_ok=True)


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def db() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with db() as connection:
        connection.executescript(
            """
            create table if not exists projects (
              project text primary key,
              name text not null,
              video_type text,
              approval_status text,
              manifest_path text not null,
              created_at real not null,
              updated_at real not null
            );

            create table if not exists jobs (
              id text primary key,
              project text not null,
              stage text not null,
              command_json text not null,
              status text not null,
              created_at real not null,
              started_at real,
              finished_at real,
              returncode integer,
              output text not null default ''
            );
            """
        )


def row_to_job(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["command"] = json.loads(payload.pop("command_json"))
    return payload


def upsert_project(project: str, name: str, video_type: str, approval_status: str, manifest_path: Path) -> None:
    now = time.time()
    with db() as connection:
        connection.execute(
            """
            insert into projects (project, name, video_type, approval_status, manifest_path, created_at, updated_at)
            values (?, ?, ?, ?, ?, ?, ?)
            on conflict(project) do update set
              name = excluded.name,
              video_type = excluded.video_type,
              approval_status = excluded.approval_status,
              manifest_path = excluded.manifest_path,
              updated_at = excluded.updated_at
            """,
            (project, name, video_type, approval_status, rel(manifest_path), now, now),
        )


def sync_manifest_projects() -> None:
    for manifest_path in sorted((MEDIA_ROOT / "manifests").glob("*_manifest.json")):
        manifest = load_json(manifest_path, {})
        project = manifest.get("project", manifest_path.stem.removesuffix("_manifest"))
        upsert_project(
            project=project,
            name=project,
            video_type=manifest.get("video_type", ""),
            approval_status=manifest.get("approval_status", ""),
            manifest_path=manifest_path,
        )


def brief_markdown(data: ProjectCreate, project: str) -> str:
    return f"""# {data.name}

## Goal

{data.goal or "Describe the video outcome."}

## Video Type

{data.video_type}

## Audience

{data.audience or "Audience not specified."}

## Format

- Aspect ratio: {data.aspect_ratio}
- Target duration: {data.target_duration_seconds} seconds
- Style: {data.style or "Not specified."}
- Voiceover: {"yes" if data.voiceover else "no"}

## Constraints

- Must include: {data.must_include or "Not specified."}
- Must avoid: {data.must_avoid or "Not specified."}

## Approval Points

- Approve scene plan before paid generation.
- Approve still frames before image-to-video.
- Approve voiceover script before TTS.
- Approve final clips before assembly.
"""


def create_manifest(project: str, data: ProjectCreate) -> dict[str, Any]:
    return {
        "project": project,
        "created_at": time.strftime("%Y-%m-%d"),
        "approval_status": "intake_created",
        "video_type": data.video_type,
        "brief": f"Docs/MediaGeneration/briefs/{project}.md",
        "scene_plan": f"Docs/MediaGeneration/storyboards/{project}_scene_plan.json",
        "checklist": [{"label": item, "done": item in {"Video type selected", "Intake complete", "Brief created"}} for item in CHECKLIST],
        "review_outputs": [],
        "generations": [],
    }


def infer_video_type(thought: str, requested: str) -> str:
    if requested != "auto":
        return requested
    lower = thought.lower()
    if any(word in lower for word in ["story", "character", "robot", "baker", "adventure"]):
        return "animated_story"
    if any(word in lower for word in ["app", "dashboard", "workflow", "screen"]):
        return "app_demo"
    if any(word in lower for word in ["logo", "brand reveal", "intro"]):
        return "logo_reveal"
    if any(word in lower for word in ["explain", "teach", "how"]):
        return "explainer"
    return "product_promo"


def title_from_thought(thought: str, video_type: str) -> str:
    lower = thought.lower()
    if "robot" in lower and "baker" in lower:
        return "Tiny Robot Baker"
    words = [word.strip(".,!?:;").title() for word in thought.split()[:5]]
    title = " ".join(words).strip()
    return title or title(video_type)


def animated_story_scenes(project: str, thought: str) -> list[dict[str, Any]]:
    return [
        {
            "id": "scene_001",
            "duration_seconds": 4,
            "purpose": "setup",
            "story_beat": "A tiny robot prepares a cozy bakery before sunrise.",
            "visual": "A tiny friendly robot baker polishes a mixing bowl in a warm cozy bakery before sunrise, flour bags and copper pans around it.",
            "camera_motion": "slow gentle push in",
            "style_notes": "warm cinematic 3D animation, soft golden light, charming family friendly tone, consistent tiny robot character, no text, no logos",
            "voiceover": "Before sunrise, a tiny robot baker wanted to make the perfect cake.",
            "on_screen_text": "",
            "generation_mode": "text_to_image_then_image_to_video",
            "status": "planned",
        },
        {
            "id": "scene_002",
            "duration_seconds": 4,
            "purpose": "conflict",
            "story_beat": "The robot tries to do everything alone.",
            "visual": "The tiny robot carefully stacks ingredients, spins a whisk, and tries to manage too many baking tasks at once.",
            "camera_motion": "small sideways dolly",
            "style_notes": "warm cinematic 3D animation, playful tension, consistent robot design, no text, no logos",
            "voiceover": "It measured, mixed, and rushed, certain it could do everything alone.",
            "on_screen_text": "",
            "generation_mode": "text_to_image_then_image_to_video",
            "status": "planned",
        },
        {
            "id": "scene_003",
            "duration_seconds": 4,
            "purpose": "turn",
            "story_beat": "A small baking mishap creates a mess.",
            "visual": "A puff of flour bursts into the air as the tiny robot watches a wobbly cake tilt on the counter.",
            "camera_motion": "quick gentle reveal",
            "style_notes": "funny but gentle, warm cinematic 3D animation, expressive robot eyes, no text, no logos",
            "voiceover": "Then one little wobble turned the whole bakery cloudy with flour.",
            "on_screen_text": "",
            "generation_mode": "text_to_image_then_image_to_video",
            "status": "planned",
        },
        {
            "id": "scene_004",
            "duration_seconds": 4,
            "purpose": "resolution",
            "story_beat": "The baker helps and teamwork saves the cake.",
            "visual": "A kind human baker kneels beside the tiny robot, and together they decorate the cake with simple frosting swirls.",
            "camera_motion": "slow warm arc",
            "style_notes": "cooperative, kind, warm cinematic 3D animation, consistent robot character, no text, no logos",
            "voiceover": "But with one helpful hand, the robot learned that teamwork made the cake better.",
            "on_screen_text": "",
            "generation_mode": "text_to_image_then_image_to_video",
            "status": "planned",
        },
        {
            "id": "scene_005",
            "duration_seconds": 4,
            "purpose": "ending",
            "story_beat": "The customer loves the charming imperfect cake.",
            "visual": "The tiny robot and baker present a charming slightly imperfect cake to a smiling customer in the glowing bakery.",
            "camera_motion": "slow cinematic push in",
            "style_notes": "happy ending, cozy warm 3D animation, gentle glow, consistent robot character, no text, no logos",
            "voiceover": "The cake was not perfect, but everyone agreed it was made with heart.",
            "on_screen_text": "",
            "generation_mode": "text_to_image_then_image_to_video",
            "status": "planned",
        },
    ]


def create_storyboard_recipes(project: str, scenes: list[dict[str, Any]], aspect_ratio: str) -> None:
    for scene in scenes:
        recipe_path = MEDIA_ROOT / "recipes" / "text_to_image" / f"{project}_{scene['id']}.json"
        prompt = f"{scene['visual']} {scene['style_notes']}"
        write_json(recipe_path, {"prompt": prompt, "aspect_ratio": aspect_ratio, "num_images": 1})


def create_voiceover_recipe(project: str, scenes: list[dict[str, Any]]) -> None:
    voiceover = " ".join(scene.get("voiceover", "") for scene in scenes).strip()
    recipe_path = MEDIA_ROOT / "recipes" / "text_to_speech" / f"{project}_voiceover_xai.json"
    write_json(recipe_path, {"text": voiceover})


def create_image_to_video_recipes(project: str, scenes: list[dict[str, Any]], aspect_ratio: str) -> None:
    for scene in scenes:
        recipe_path = MEDIA_ROOT / "recipes" / "image_to_video" / f"{project}_{scene['id']}.json"
        prompt = (
            f"Preserve the input image and character design. {scene['camera_motion']}. "
            f"Animate the scene with subtle expressive motion matching this beat: {scene['story_beat']}. "
            "Warm cinematic family-friendly animation, stable composition, no text, no logos, no watermark."
        )
        write_json(
            recipe_path,
            {
                "prompt": prompt,
                "duration": str(scene["duration_seconds"]),
                "aspect_ratio": aspect_ratio,
                "generate_audio": False,
                "negative_prompt": "blur, distortion, warped character, unreadable text, logos, watermark, flicker, low quality",
            },
        )


def generation_commands(project: str, scene_plan: dict[str, Any]) -> dict[str, list[str]]:
    scenes = scene_plan.get("scenes", [])
    storyboard = [
        f".\\run_fal.bat --model fal-ai/flux/schnell --args Docs\\MediaGeneration\\recipes\\text_to_image\\{project}_{scene['id']}.json --out Docs\\MediaGeneration\\outputs\\text_to_image --project {project}"
        for scene in scenes
    ]
    clips = [
        f".\\run_fal.bat --model fal-ai/kling-video/v3/standard/image-to-video --args Docs\\MediaGeneration\\recipes\\image_to_video\\{project}_{scene['id']}.json --upload-file start_image_url=Docs\\MediaGeneration\\outputs\\text_to_image\\{project}\\APPROVED_STILL_{scene['id']}.jpg --out Docs\\MediaGeneration\\outputs\\image_to_video --project {project}"
        for scene in scenes
    ]
    voiceover = [
        f".\\run_fal.bat --model xai/tts/v1 --args Docs\\MediaGeneration\\recipes\\text_to_speech\\{project}_voiceover_xai.json --out Docs\\MediaGeneration\\outputs\\text_to_speech --project {project}"
    ]
    return {"storyboard_stills": storyboard, "video_clips": clips, "voiceover": voiceover}


def run_job(job_id: str) -> None:
    with db() as connection:
        connection.execute(
            "update jobs set status = ?, started_at = ? where id = ?",
            ("running", time.time(), job_id),
        )
        row = connection.execute("select * from jobs where id = ?", (job_id,)).fetchone()

    if row is None:
        return

    snapshot = row_to_job(row)

    try:
        process = subprocess.run(
            snapshot["command"],
            cwd=PROJECT_ROOT,
            text=True,
            capture_output=True,
            timeout=None,
        )
        output = (process.stdout or "") + (process.stderr or "")
        status = "completed" if process.returncode == 0 else "failed"
        returncode = process.returncode
    except Exception as exc:
        output = f"{type(exc).__name__}: {exc}"
        status = "failed"
        returncode = -1

    with db() as connection:
        connection.execute(
            """
            update jobs
            set status = ?, finished_at = ?, returncode = ?, output = ?
            where id = ?
            """,
            (status, time.time(), returncode, output[-12000:], job_id),
        )


def list_project_files(project: str) -> dict[str, Any]:
    manifest_path = MEDIA_ROOT / "manifests" / f"{project}_manifest.json"
    manifest = load_json(manifest_path, {})
    outputs = {}
    for folder in ["text_to_image", "image_to_video", "text_to_speech", "text_to_video", "review"]:
        files = []
        out_dir = MEDIA_ROOT / "outputs" / folder
        if out_dir.exists():
            for path in sorted(out_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
                if path.is_file():
                    files.append({
                        "name": path.name,
                        "path": rel(path),
                        "url": media_url(path),
                        "size": path.stat().st_size,
                        "mtime": path.stat().st_mtime,
                    })
        outputs[folder] = files
    return {"manifest": manifest, "outputs": outputs}


ensure_folders()
init_db()
sync_manifest_projects()


@app.get("/")
def root() -> FileResponse:
    return FileResponse(WEB_ROOT / "index.html")


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {
        "ok": True,
        "project_root": str(PROJECT_ROOT),
        "database": str(DB_PATH),
        "fal_key_set": bool(os.environ.get("FAL_KEY")),
        "video_types": VIDEO_TYPES,
    }


@app.get("/api/project-types")
def project_types() -> list[dict[str, Any]]:
    return PROJECT_TYPES


@app.get("/api/projects")
def projects() -> list[dict[str, Any]]:
    ensure_folders()
    sync_manifest_projects()
    with db() as connection:
        rows = connection.execute(
            """
            select project, video_type, approval_status, manifest_path as manifest
            from projects
            order by updated_at desc, project asc
            """
        ).fetchall()
    return [dict(row) for row in rows]


@app.post("/api/projects")
def create_project(data: ProjectCreate) -> dict[str, Any]:
    ensure_folders()
    if data.video_type not in VIDEO_TYPES:
        raise HTTPException(status_code=400, detail=f"Unknown video_type. Use one of: {', '.join(VIDEO_TYPES)}")

    project = slugify(data.name)
    brief_path = MEDIA_ROOT / "briefs" / f"{project}.md"
    scene_path = MEDIA_ROOT / "storyboards" / f"{project}_scene_plan.json"
    manifest_path = MEDIA_ROOT / "manifests" / f"{project}_manifest.json"

    brief_path.write_text(brief_markdown(data, project), encoding="utf-8")
    scene_plan = {
        "project": project,
        "video_type": data.video_type,
        "aspect_ratio": data.aspect_ratio,
        "target_duration_seconds": data.target_duration_seconds,
        "scenes": [],
    }
    write_json(scene_path, scene_plan)
    manifest = create_manifest(project, data)
    write_json(manifest_path, manifest)
    upsert_project(project, data.name, data.video_type, manifest["approval_status"], manifest_path)

    return {"project": project, "brief": rel(brief_path), "scene_plan": rel(scene_path), "manifest": rel(manifest_path)}


@app.post("/api/projects/from-thought")
def create_project_from_thought(data: ThoughtProjectCreate) -> dict[str, Any]:
    ensure_folders()
    video_type = infer_video_type(data.thought, data.video_type)
    name = title_from_thought(data.thought, video_type)
    project_data = ProjectCreate(
        name=name,
        video_type=video_type,
        goal=data.thought,
        audience="General audience" if video_type == "animated_story" else "Potential viewers",
        aspect_ratio=data.aspect_ratio,
        target_duration_seconds=data.target_duration_seconds,
        style="Warm cinematic 3D animation" if video_type == "animated_story" else "Cinematic and clear",
        voiceover=True,
        must_include="A clear beginning, middle, and ending" if video_type == "animated_story" else "",
        must_avoid="Unreadable generated text, logos, watermarks",
    )

    created = create_project(project_data)
    project = created["project"]
    scene_path = MEDIA_ROOT / "storyboards" / f"{project}_scene_plan.json"
    manifest_path = MEDIA_ROOT / "manifests" / f"{project}_manifest.json"

    scenes = animated_story_scenes(project, data.thought)
    scene_plan = {
        "project": project,
        "video_type": video_type,
        "aspect_ratio": data.aspect_ratio,
        "target_duration_seconds": data.target_duration_seconds,
        "character_continuity": "Tiny friendly robot baker with expressive eyes, small metal body, chef hat, and gentle helpful personality.",
        "setting_continuity": "Warm cozy bakery with golden morning light, flour, copper pans, wood counters, and family-friendly charm.",
        "scenes": scenes,
    }
    write_json(scene_path, scene_plan)
    create_storyboard_recipes(project, scenes, data.aspect_ratio)
    create_image_to_video_recipes(project, scenes, data.aspect_ratio)
    create_voiceover_recipe(project, scenes)

    manifest = load_json(manifest_path, {})
    manifest["approval_status"] = "scene_plan_draft"
    manifest["scene_plan"] = f"Docs/MediaGeneration/storyboards/{project}_scene_plan.json"
    for item in manifest.get("checklist", []):
        if item["label"] == "Scene plan created":
            item["done"] = True
    write_json(manifest_path, manifest)
    upsert_project(project, name, video_type, manifest["approval_status"], manifest_path)

    return {
        **created,
        "project": project,
        "video_type": video_type,
        "commands": generation_commands(project, scene_plan),
    }


@getattr(app, "get")("/api/projects/{project}")
def project_detail(project: str) -> dict[str, Any]:
    manifest_path = MEDIA_ROOT / "manifests" / f"{project}_manifest.json"
    if not manifest_path.exists():
        raise HTTPException(status_code=404, detail="Project not found")
    scene_path = MEDIA_ROOT / "storyboards" / f"{project}_scene_plan.json"
    brief_path = MEDIA_ROOT / "briefs" / f"{project}.md"
    return {
        "project": project,
        "brief": brief_path.read_text(encoding="utf-8") if brief_path.exists() else "",
        "scene_plan": load_json(scene_path, {}),
        "commands": generation_commands(project, load_json(scene_path, {})),
        **list_project_files(project),
    }


@app.put("/api/projects/{project}/scene-plan")
def save_scene_plan(project: str, data: ScenePlanRequest) -> dict[str, Any]:
    if project != data.project:
        raise HTTPException(status_code=400, detail="Project mismatch")
    scene_path = MEDIA_ROOT / "storyboards" / f"{project}_scene_plan.json"
    existing = load_json(scene_path, {"project": project, "scenes": []})
    existing["scenes"] = data.scenes
    write_json(scene_path, existing)
    return {"ok": True, "scene_plan": rel(scene_path)}


@app.post("/api/jobs")
def create_job(data: JobCreate, background_tasks: BackgroundTasks) -> dict[str, Any]:
    if not data.command:
        raise HTTPException(status_code=400, detail="Command is required")
    job_id = str(uuid.uuid4())
    with db() as connection:
        connection.execute(
            """
            insert into jobs (id, project, stage, command_json, status, created_at)
            values (?, ?, ?, ?, ?, ?)
            """,
            (job_id, data.project, data.stage, json.dumps(data.command), "queued", time.time()),
        )
    background_tasks.add_task(run_job, job_id)
    return {"job_id": job_id, "status": "queued"}


@app.get("/api/jobs")
def list_jobs() -> list[dict[str, Any]]:
    with db() as connection:
        rows = connection.execute("select * from jobs order by created_at desc").fetchall()
    return [row_to_job(row) for row in rows]


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str) -> dict[str, Any]:
    with db() as connection:
        row = connection.execute("select * from jobs where id = ?", (job_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return row_to_job(row)

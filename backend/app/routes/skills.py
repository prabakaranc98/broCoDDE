"""
BroCoDDE — Skills API Routes
GET /skills — list all available skills (name + description)
GET /skills/{name} — load full SKILL.md content for a skill
GET /skills/{name}/references/{ref} — load a reference file
"""

from fastapi import APIRouter, HTTPException

from app.agents.tools import skill_list, skill_load, skill_load_reference

router = APIRouter()


@router.get("")
async def list_skills():
    """List all available skills with names and one-line descriptions."""
    return await skill_list()


@router.get("/{skill_name}")
async def get_skill(skill_name: str):
    """Load the full SKILL.md content for a named skill."""
    content = await skill_load(skill_name)
    if "not found" in content.lower():
        raise HTTPException(status_code=404, detail=content)
    return {"name": skill_name, "content": content}


@router.get("/{skill_name}/references/{ref_name}")
async def get_skill_reference(skill_name: str, ref_name: str):
    """Load a reference file from a skill's references/ directory."""
    content = await skill_load_reference(skill_name, ref_name)
    if "not found" in content.lower():
        raise HTTPException(status_code=404, detail=content)
    return {"skill": skill_name, "reference": ref_name, "content": content}

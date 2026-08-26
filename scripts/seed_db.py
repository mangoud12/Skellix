"""
scripts/seed_db.py

Seeds the Skillix database with careers, skills, career-skill mappings,
and questions from the JSON data files.

Usage:
    python -m scripts.seed_db
    # or from project root:
    python scripts/seed_db.py
"""

import json
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Ensure project root is on sys.path when run directly
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from models.career import Career, CareerSkill
from models.skill import Skill
from models.question import Question

# ---------------------------------------------------------------------------
# Data file paths
# ---------------------------------------------------------------------------
DATA_DIR = PROJECT_ROOT / "data"
QUESTIONS_DIR = DATA_DIR / "questions"

QUESTION_FILES = [
    "python.json",
    "machine_learning.json",
    "deep_learning.json",
    "javascript.json",
    "react.json",
    "sql.json",
    "rest_apis.json",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_json(path: Path) -> list | dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def seed_careers(db: Session) -> dict[int, Career]:
    """Seed Career rows. Returns a dict keyed by original JSON id."""
    if db.query(Career).count() > 0:
        print("  [skip] Careers already seeded.")
        return {c.id: c for c in db.query(Career).all()}

    data = load_json(DATA_DIR / "careers.json")
    id_map: dict[int, Career] = {}
    for item in data:
        name_val = item.get("name") or item.get("title", "")
        # توليد slug تلقائي فريد في حال كان فارغاً
        raw_slug = item.get("slug")
        slug_val = raw_slug if raw_slug else name_val.lower().replace(" ", "-").replace("_", "-")

        career = Career(
            id=item["id"],
            name=name_val,
            slug=slug_val,
            description=item.get("description"),
            icon=item.get("icon"),
        )
        db.add(career)
        id_map[item["id"]] = career

    db.flush()
    print(f"  [ok] Seeded {len(data)} careers.")
    return id_map

def seed_skills(db: Session) -> dict[int, Skill]:
    """Seed Skill rows. Returns a dict keyed by original JSON id."""
    if db.query(Skill).count() > 0:
        print("  [skip] Skills already seeded.")
        return {s.id: s for s in db.query(Skill).all()}

    data = load_json(DATA_DIR / "skills.json")
    id_map: dict[int, Skill] = {}
    for item in data:
        skill = Skill(
            id=item["id"],
            name=item["name"],
            slug=item["slug"],
            description=item.get("description"),
            category=item.get("category"),
        )
        db.add(skill)
        id_map[item["id"]] = skill

    db.flush()
    print(f"  [ok] Seeded {len(data)} skills.")
    return id_map


def seed_career_skills(db: Session) -> None:
    """Seed CareerSkill association rows."""
    if db.query(CareerSkill).count() > 0:
        print("  [skip] CareerSkills already seeded.")
        return

    data = load_json(DATA_DIR / "career_skills.json")
    for item in data:
        cs = CareerSkill(
            career_id=item["career_id"],
            skill_id=item["skill_id"],
            is_core=item.get("is_core", item.get("importance") == "high"),
            weight=item.get("weight", 1.0),
            display_order=item.get("display_order", 1),
        )
        db.add(cs)

    db.flush()
    print(f"  [ok] Seeded {len(data)} career-skill mappings.")


def seed_questions(db: Session) -> None:
    """Seed Question rows from all question JSON files."""
    if db.query(Question).count() > 0:
        print("  [skip] Questions already seeded.")
        return

    total = 0
    for filename in QUESTION_FILES:
        path = QUESTIONS_DIR / filename
        if not path.exists():
            print(f"  [warn] Question file not found: {path}")
            continue

        data = load_json(path)
        for item in data:
            question = Question(
                skill_id=item.get("skill_id", 1),
                text=item.get("question") or item.get("text"),
                type=item.get("type", "single"),
                difficulty=item.get("difficulty", "medium"),
                points=item.get("points", 10),
                explanation=item.get("explanation", ""),
            )
            db.add(question)
            total += 1

        print(f"  [ok] Loaded {len(data)} questions from {filename}.")

    db.flush()
    print(f"  [ok] Total questions seeded: {total}.")


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def run_seed() -> None:
    print("\n=== Skillix DB Seeder ===\n")

    Base.metadata.create_all(bind=engine)
    print("[step] Ensured all tables exist.\n")

    db: Session = SessionLocal()
    try:
        print("[step] Seeding careers...")
        seed_careers(db)

        print("[step] Seeding skills...")
        seed_skills(db)

        print("[step] Seeding career-skill mappings...")
        seed_career_skills(db)

        print("[step] Seeding questions...")
        seed_questions(db)

        db.commit()
        print("\n[done] Database seeded successfully.\n")

    except Exception as exc:
        db.rollback()
        print(f"\n[error] Seed failed — rolled back. Reason: {exc}")
        raise

    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
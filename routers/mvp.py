"""Academy-ready MVP API: profiles, deterministic assessments, AI-style feedback, careers."""
from __future__ import annotations

from uuid import uuid4
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api", tags=["MVP"])

SKILLS = {
    "javascript": ("What does === compare in JavaScript?", ["Only values", "Only types", "Value and type", "Object contents"], 2, "Use strict equality when you do not want coercion."),
    "python": ("Which Python collection stores unique values?", ["list", "tuple", "set", "dict"], 2, "A set automatically removes duplicate values."),
    "react": ("Which Hook stores component state?", ["useMemo", "useState", "useEffect", "useRef"], 1, "useState holds values that trigger a re-render."),
    "fastapi": ("Which decorator creates a GET endpoint?", ["@app.get", "@app.fetch", "@app.route", "@app.read"], 0, "FastAPI maps HTTP methods with decorators such as @app.get."),
    "sql": ("Which clause filters grouped SQL results?", ["WHERE", "ORDER BY", "HAVING", "LIMIT"], 2, "HAVING filters after GROUP BY has created aggregate groups."),
    "typescript": ("What does an interface describe?", ["A runtime class", "An object shape", "A database table", "A CSS selector"], 1, "Interfaces provide static type contracts."),
    "machine-learning": ("What is overfitting?", ["Good generalization", "Memorizing training data", "Too little data", "A database error"], 1, "Overfit models score well on training data but fail on unseen examples."),
    "git": ("Which command creates a commit?", ["git push", "git merge", "git commit", "git clone"], 2, "Commit records staged changes in your local repository."),
}
RAW_CAREERS = [
    ("Frontend Developer", ["JavaScript", "TypeScript", "React"]), ("Backend Developer", ["Python", "FastAPI", "SQL"]), ("Full Stack Developer", ["JavaScript", "React", "Python", "SQL"]), ("Mobile Developer", ["JavaScript", "TypeScript", "React"]), ("DevOps Engineer", ["Python", "Git", "SQL"]), ("Cloud Engineer", ["Python", "Git", "SQL"]), ("Data Analyst", ["SQL", "Python", "JavaScript"]), ("Data Engineer", ["Python", "SQL", "Git"]), ("Machine Learning Engineer", ["Python", "Machine Learning", "SQL"]), ("AI Engineer", ["Python", "Machine Learning", "FastAPI"]), ("MLOps Engineer", ["Python", "Machine Learning", "Git"]), ("QA Automation Engineer", ["Python", "JavaScript", "Git"]), ("Cybersecurity Analyst", ["Python", "SQL", "Git"]), ("Site Reliability Engineer", ["Python", "Git", "SQL"]), ("Product Manager", ["SQL", "Python", "JavaScript"]), ("Product Designer", ["JavaScript", "React", "TypeScript"]), ("UX Researcher", ["SQL", "Python", "JavaScript"]), ("Business Intelligence Developer", ["SQL", "Python", "Git"]), ("Database Administrator", ["SQL", "Python", "Git"]), ("Solutions Architect", ["Python", "FastAPI", "SQL"]), ("Technical Writer", ["Git", "Python", "JavaScript"]), ("Game Developer", ["JavaScript", "TypeScript", "Git"]), ("AR/VR Developer", ["JavaScript", "TypeScript", "React"]), ("Blockchain Developer", ["JavaScript", "TypeScript", "Git"]), ("Embedded Systems Engineer", ["Python", "Git", "SQL"]), ("Systems Engineer", ["Python", "Git", "SQL"]), ("Network Engineer", ["Python", "Git", "SQL"]), ("Automation Engineer", ["Python", "FastAPI", "Git"]), ("Platform Engineer", ["Python", "Git", "FastAPI"]), ("API Integration Engineer", ["Python", "FastAPI", "JavaScript"]), ("Software Engineer", ["Python", "JavaScript", "Git"]), ("Software Architect", ["Python", "TypeScript", "SQL"]), ("Engineering Manager", ["Python", "Git", "SQL"]), ("Analytics Engineer", ["SQL", "Python", "Git"]), ("Data Scientist", ["Python", "Machine Learning", "SQL"]), ("NLP Engineer", ["Python", "Machine Learning", "FastAPI"]), ("Computer Vision Engineer", ["Python", "Machine Learning", "Git"]), ("Growth Engineer", ["JavaScript", "SQL", "React"]), ("Technical Support Engineer", ["Python", "SQL", "Git"]), ("Developer Advocate", ["JavaScript", "Python", "Git"]),
]
RESOURCE_BY_KEYWORD = {
    "Machine Learning": ("Google ML Crash Course", "https://developers.google.com/machine-learning/crash-course"),
    "SQL": ("SQLBolt", "https://sqlbolt.com/"),
    "React": ("React Learn", "https://react.dev/learn"),
    "FastAPI": ("FastAPI Tutorial", "https://fastapi.tiangolo.com/tutorial/"),
    "Git": ("Pro Git", "https://git-scm.com/book/en/v2"),
    "JavaScript": ("MDN JavaScript", "https://developer.mozilla.org/en-US/docs/Web/JavaScript"),
    "Python": ("Python Tutorial", "https://docs.python.org/3/tutorial/"),
}
CAREERS = [{
    "id": f"career-{i+1}", "title": title,
    "description": f"Build and improve products as a {title}, combining practical delivery with thoughtful problem solving.",
    "requiredSkills": skills,
    "pathSteps": [f"Learn the foundations of {skills[0]}", f"Build a portfolio project using {skills[1]}", f"Ship, document, and collaborate with {skills[2]}"],
    "links": [
        {"label": RESOURCE_BY_KEYWORD.get(skills[0], ("Roadmap.sh", "https://roadmap.sh/"))[0], "url": RESOURCE_BY_KEYWORD.get(skills[0], ("Roadmap.sh", "https://roadmap.sh/"))[1]},
        {"label": "Role roadmap on Roadmap.sh", "url": "https://roadmap.sh/"},
    ],
} for i, (title, skills) in enumerate(RAW_CAREERS)]
PROFILES: dict[str, dict] = {}

class ProfileIn(BaseModel):
    languages: list[str] = Field(min_length=1, max_length=20)
    skills: list[str] = Field(default_factory=list, max_length=30)
class EvaluateIn(BaseModel):
    profileId: str
    skillId: str
    userAnswer: str
class FeedbackIn(BaseModel):
    skillId: str
    userAnswer: str
    evaluationResult: dict

@router.post("/profile")
def create_profile(payload: ProfileIn):
    profile_id = uuid4().hex
    PROFILES[profile_id] = payload.model_dump()
    return {"profileId": profile_id, "status": "created", "profile": PROFILES[profile_id]}

@router.get("/skills")
def list_skills():
    return {"skills": [{"id": key, "title": key.replace("-", " ").title(), "task": value[0]} for key, value in SKILLS.items()]}

@router.post("/evaluate")
def evaluate(payload: EvaluateIn):
    if payload.profileId not in PROFILES: raise HTTPException(404, "Profile session not found. Start with Explore me.")
    if payload.skillId not in SKILLS: raise HTTPException(422, "Unsupported skill. Select a listed MVP skill.")
    _, options, correct_index, improvement = SKILLS[payload.skillId]
    answer = payload.userAnswer.strip()
    correct = answer == options[correct_index]
    score = 100 if correct else 35 if answer else 0
    mistakes = [] if correct else [{"category": "concept_accuracy", "message": "The selected answer does not match the core concept.", "hint": improvement}]
    rubric = {"concept_accuracy": {"pointsEarned": 7 if correct else 2 if answer else 0, "pointsPossible": 7, "percent": score}, "response_quality": {"pointsEarned": 3 if answer else 0, "pointsPossible": 3, "percent": 100 if answer else 0}}
    return {"score": score, "rubric": rubric, "mistakes": mistakes, "evaluationSummary": "Great work — you selected the correct answer." if correct else "This concept needs one more focused review.", "correctAnswer": options[correct_index], "suggestedImprovement": improvement}

@router.post("/ai-feedback")
def feedback(payload: FeedbackIn):
    result = payload.evaluationResult
    passed = result.get("score", 0) >= 70
    skill = payload.skillId.replace("-", " ").title()
    return {"summary": f"Your {skill} baseline is {'strong' if passed else 'developing'}.", "mistakes": [] if passed else [m.get("message", "Review the core concept.") for m in result.get("mistakes", [])], "why": ["The rubric weights conceptual accuracy most heavily.", "A deliberate retry builds reliable recall."], "fix_steps": ["Read the suggested improvement.", "Compare the correct answer with your response.", "Retry a small practice task before moving on."], "next_task": {"skillId": "react" if payload.skillId != "react" else "typescript", "taskTitle": "Complete the next foundations check"}}

@router.get("/careers")
def careers(q: str = "", skills: str = "", score: float | None = None):
    query = q.lower().strip()
    results = [c for c in CAREERS if not query or query in c["title"].lower() or any(query in s.lower() for s in c["requiredSkills"])]
    # Assessment signals are optional. When present, higher overlap is shown
    # first so the Career Hub can recommend roles grounded in actual results.
    learned = {item.strip().lower().replace("_", " ") for item in skills.split(",") if item.strip()}
    if learned:
        results.sort(key=lambda career: sum(skill.lower() in learned for skill in career["requiredSkills"]), reverse=True)
    return {"careers": results, "total": len(results)}

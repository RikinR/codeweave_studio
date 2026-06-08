"""Shared sample state for independent agent smoke tests."""

SAMPLE_GOALS = {
    "feature_name": "User profile API",
    "request_type": "feature",
    "scope": [
        "Add GET /api/users/{id}/profile endpoint",
        "Return display name and avatar URL",
    ],
    "constraints": [
        "Must use existing auth middleware",
        "No breaking changes to current user model",
    ],
    "non_goals": [
        "Avatar upload UI",
        "Profile editing",
    ],
    "assumptions": [
        "Avatar URL stored on user record as optional string field",
    ],
    "success_criteria": [
        "Authenticated users can fetch profile by user id",
        "Returns 404 for unknown user id",
        "Unit tests cover happy path and 404",
    ],
}

SAMPLE_RELEVENT_CONTEXT = {
    "architecture_summary": "FastAPI backend with SQLAlchemy models under src/",
    "affected_files": [
        {"path": "src/api/users.py", "reason": "Existing user routes"},
        {"path": "src/models/user.py", "reason": "User ORM model"},
    ],
    "affected_functions": [
        {"name": "get_user", "file_path": "src/api/users.py", "reason": "Existing lookup"},
    ],
    "call_chains": [
        {"entry_function": "get_user", "chain": ["router", "get_user", "UserRepository.find"]},
    ],
    "entry_points": ["src/api/users.py"],
    "dependencies": ["fastapi", "sqlalchemy"],
    "retrieval_sources": ["semantic_search", "read_file"],
    "context_gaps": ["Exact avatar column name not confirmed in schema"],
}

SAMPLE_PLAN = {
    "summary": "Add profile endpoint and optional avatar_url column with migration.",
    "steps": [
        {
            "step_number": 1,
            "title": "Add avatar_url column",
            "description": "Migration and model update for optional avatar URL",
            "affected_files": ["src/models/user.py", "migrations/001_avatar.py"],
            "risk_level": "medium",
            "verification_steps": ["Run migration up and down"],
        },
        {
            "step_number": 2,
            "title": "Add profile endpoint",
            "description": "GET /api/users/{id}/profile returning name and avatar_url",
            "affected_files": ["src/api/users.py"],
            "risk_level": "low",
            "verification_steps": ["pytest tests/api/test_users.py"],
        },
    ],
    "risks": ["Migration on large user table may lock briefly"],
    "rollback_strategy": "Revert migration and remove endpoint",
    "completion_criteria": ["Endpoint returns profile JSON", "Tests pass"],
}

SAMPLE_BACKEND_TASKS = {
    "tasks": [
        {
            "id": "be-1",
            "title": "Profile endpoint",
            "description": "GET /api/users/{id}/profile returns display_name, avatar_url",
            "owner": "backend",
            "dependencies": ["db-1"],
            "acceptance_criteria": ["Returns 200 with profile JSON", "Returns 404 for missing user"],
            "affected_files": ["src/api/users.py"],
        }
    ]
}

SAMPLE_FRONTEND_TASKS = {
    "tasks": [
        {
            "id": "fe-1",
            "title": "Profile page",
            "description": "Display user profile from GET /api/users/{id}/profile",
            "owner": "frontend",
            "dependencies": ["be-1"],
            "acceptance_criteria": ["Shows name and avatar", "Handles 404 state"],
            "affected_files": ["src/pages/Profile.tsx"],
        }
    ]
}

SAMPLE_DATABASE_TASKS = {
    "tasks": [
        {
            "id": "db-1",
            "title": "Avatar column migration",
            "description": "Add nullable avatar_url to users table",
            "owner": "database",
            "dependencies": [],
            "acceptance_criteria": ["Migration applies cleanly", "ORM model matches schema"],
            "affected_files": ["migrations/001_avatar.py", "src/models/user.py"],
        }
    ]
}

SAMPLE_PATCHES = {
    "src/api/users.py": {
        "file_path": "src/api/users.py",
        "reason": "Add profile endpoint",
        "diff": (
            "--- a/src/api/users.py\n"
            "+++ b/src/api/users.py\n"
            "@@ -10,3 +10,12 @@\n"
            "+@router.get('/users/{user_id}/profile')\n"
            "+def get_profile(user_id: int):\n"
            "+    user = repo.find(user_id)\n"
            "+    if not user:\n"
            "+        raise HTTPException(404)\n"
            "+    return {'display_name': user.name, 'avatar_url': user.avatar_url}\n"
        ),
    },
    "src/models/user.py": {
        "file_path": "src/models/user.py",
        "reason": "Add avatar_url field",
        "diff": (
            "--- a/src/models/user.py\n"
            "+++ b/src/models/user.py\n"
            "@@ -5,6 +5,7 @@\n"
            " class User(Base):\n"
            "     name: str\n"
            "+    avatar_url: str | None = None\n"
        ),
    },
}

SAMPLE_BACKEND_RESULT = {
    "summary": "Added profile endpoint",
    "modified_files": ["src/api/users.py"],
    "patches": [SAMPLE_PATCHES["src/api/users.py"]],
    "risks": [],
    "open_questions": [],
}

SAMPLE_MIGRATION_PATCH = {
    "file_path": "migrations/001_avatar.py",
    "reason": "Add avatar_url column",
    "diff": (
        "--- a/migrations/001_avatar.py\n"
        "+++ b/migrations/001_avatar.py\n"
        "@@ -0,0 +1,11 @@\n"
        "+from alembic import op\n"
        "+import sqlalchemy as sa\n"
        "+\n"
        "+revision = '001_avatar'\n"
        "+down_revision = None\n"
        "+\n"
        "+def upgrade():\n"
        "+    op.add_column('users', sa.Column('avatar_url', sa.String(), nullable=True))\n"
        "+\n"
        "+def downgrade():\n"
        "+    op.drop_column('users', 'avatar_url')\n"
    ),
}

SAMPLE_DATABASE_RESULT = {
    "summary": "Added avatar_url migration",
    "modified_files": ["src/models/user.py", "migrations/001_avatar.py"],
    "patches": [SAMPLE_PATCHES["src/models/user.py"], SAMPLE_MIGRATION_PATCH],
    "risks": ["Migration lock on large table"],
    "open_questions": [],
}

SAMPLE_FRONTEND_PATCH = {
    "file_path": "src/pages/Profile.tsx",
    "reason": "Profile UI wired to backend contract",
    "diff": (
        "--- a/src/pages/Profile.tsx\n"
        "+++ b/src/pages/Profile.tsx\n"
        "@@ -1,3 +1,28 @@\n"
        "+import { useEffect, useState } from 'react';\n"
        "+\n"
        "+type ProfileResponse = { display_name: string; avatar_url: string | null };\n"
        "+\n"
        "+export function Profile({ userId }: { userId: string }) {\n"
        "+  const [profile, setProfile] = useState<ProfileResponse | null>(null);\n"
        "+  const [error, setError] = useState<string | null>(null);\n"
        "+\n"
        "+  useEffect(() => {\n"
        "+    fetch(`/api/users/${userId}/profile`)\n"
        "+      .then((res) => {\n"
        "+        if (!res.ok) throw new Error('not found');\n"
        "+        return res.json();\n"
        "+      })\n"
        "+      .then(setProfile)\n"
        "+      .catch(() => setError('User not found'));\n"
        "+  }, [userId]);\n"
        "+\n"
        "+  if (error) return <div>{error}</div>;\n"
        "+  if (!profile) return <div>Loading...</div>;\n"
        "+  return <div><h1>{profile.display_name}</h1><img src={profile.avatar_url ?? ''} /></div>;\n"
        "+}\n"
    ),
}

SAMPLE_FRONTEND_RESULT = {
    "summary": "Added profile page",
    "modified_files": ["src/pages/Profile.tsx"],
    "patches": [SAMPLE_FRONTEND_PATCH],
    "risks": [],
    "open_questions": [],
}

SAMPLE_INTEGRATED_STATE = {
    "summary": "Profile feature integrated across API, schema, and UI",
    "conflict_resolutions": [],
    "contract_validations": [
        "Profile endpoint response matches frontend Profile.tsx expectations",
    ],
    "integration_blocked": False,
}

SAMPLE_TEST_RESULTS = {
    "build_status": "passed",
    "lint_status": "passed",
    "typecheck_status": "passed",
    "tests_passed": 12,
    "tests_failed": 0,
    "tests_skipped": 1,
    "failures": [],
}

SAMPLE_REVIEW_ISSUES = [
    {
        "severity": "medium",
        "file_path": "src/api/users.py",
        "line_number": 14,
        "description": "Missing auth check on profile endpoint",
        "recommendation": "Apply require_auth dependency to route",
    }
]

SAMPLE_SKEPTIC_FINDINGS = [
    {
        "category": "edge_case",
        "severity": "medium",
        "description": "Profile endpoint may leak email if serializer expands",
        "scenario": "Future field added to response without review",
        "affected_files": ["src/api/users.py"],
        "confidence": "medium",
        "recommendation": "Use explicit response schema",
    }
]

SAMPLE_PRODUCTION_CHANGES = {
    "summary": "Improved typing and logging on profile endpoint",
    "changes": [
        {
            "file_path": "src/api/users.py",
            "change_type": "typing",
            "description": "Added ProfileResponse model",
            "rationale": "Prevents accidental field leakage",
        }
    ],
    "patches": [],
}

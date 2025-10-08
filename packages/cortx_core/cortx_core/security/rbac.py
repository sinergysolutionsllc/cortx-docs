from enum import StrEnum


class Role(StrEnum):
    ADMIN = "admin"
    ENGINEER = "engineer"
    ANALYST = "analyst"
    VIEWER = "viewer"
    SERVICE = "service"


POLICY = {
    Role.ADMIN: {"*": ["read", "write", "execute"]},
    Role.ENGINEER: {
        "pipelines": ["read", "write"],
        "prompts": ["read", "write"],
        "audits": ["read"],
    },
    Role.ANALYST: {"runs": ["read"], "reports": ["read"], "prompts": ["read"]},
    Role.VIEWER: {"runs": ["read"], "reports": ["read"]},
    Role.SERVICE: {"*": ["execute", "read"]},
}


def can(role: Role, resource: str, action: str) -> bool:
    rules = POLICY.get(role, {})
    if "*" in rules and action in rules["*"]:
        return True
    return action in rules.get(resource, [])

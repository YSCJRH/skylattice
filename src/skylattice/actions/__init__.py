"""Action interfaces and concrete adapters."""

from .git import GitAdapter, GitCommandError
from .gitlab import GitLabAdapter
from .github import GitHubAdapter, GitHubRepoRef
from .interfaces import ActionAdapter, ActionRequest, ActionResult, ActionScope, ApprovalRequirement
from .repo import RepoWorkspaceAdapter

__all__ = [
    "ActionAdapter",
    "ActionRequest",
    "ActionResult",
    "ActionScope",
    "ApprovalRequirement",
    "GitAdapter",
    "GitCommandError",
    "GitLabAdapter",
    "GitHubAdapter",
    "GitHubRepoRef",
    "RepoWorkspaceAdapter",
]

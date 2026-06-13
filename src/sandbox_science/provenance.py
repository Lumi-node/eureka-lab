from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

import git
from pydantic import BaseModel


class CommitInfo(BaseModel):
    """Metadata for a single Git commit."""

    sha: str
    message: str
    timestamp: datetime
    files: list[str]
    author: str


class MergeResult(BaseModel):
    """Outcome of a merge between two repositories."""

    success: bool
    sha: str | None = None
    conflicts: list[str] = []


class GitRepo:
    """Per-run lightweight Git repository for artifact provenance."""

    def __init__(self) -> None:
        self._repo: git.Repo | None = None
        self._path: Path | None = None

    @property
    def path(self) -> Path:
        assert self._path is not None
        return self._path

    def init(self, path: Path) -> None:
        self._path = Path(path)
        self._path.mkdir(parents=True, exist_ok=True)
        self._repo = git.Repo.init(str(self._path))
        with self._repo.config_writer() as cw:
            cw.set_value("user", "name", "Sandbox Science")
            cw.set_value("user", "email", "sandbox@science.local")

    def commit(self, files: list[Path], message: str) -> CommitInfo:
        assert self._repo is not None and self._path is not None
        rel_paths: list[str] = []
        for f in files:
            p = Path(f)
            try:
                rel = str(p.relative_to(self._path))
            except ValueError:
                rel = str(p)
            rel_paths.append(rel)

        self._repo.index.add(rel_paths)
        commit_obj = self._repo.index.commit(message)
        return CommitInfo(
            sha=commit_obj.hexsha,
            message=message,
            timestamp=datetime.fromtimestamp(commit_obj.committed_date),
            files=rel_paths,
            author=str(commit_obj.author),
        )

    def log(self) -> list[CommitInfo]:
        assert self._repo is not None
        commits: list[CommitInfo] = []
        for c in self._repo.iter_commits():
            file_names = list(c.stats.files.keys())
            commits.append(
                CommitInfo(
                    sha=c.hexsha,
                    message=c.message.strip(),
                    timestamp=datetime.fromtimestamp(c.committed_date),
                    files=file_names,
                    author=str(c.author),
                )
            )
        return commits

    def merge(self, other: GitRepo) -> MergeResult:
        assert self._repo is not None and other._repo is not None
        remote_name = f"merge_{id(other)}"
        self._repo.create_remote(remote_name, str(other._path))
        try:
            self._repo.remotes[remote_name].fetch()
            other_branch = other._repo.active_branch.name
            self._repo.git.merge(
                f"{remote_name}/{other_branch}",
                allow_unrelated_histories=True,
                no_edit=True,
            )
            sha = self._repo.head.commit.hexsha
            return MergeResult(success=True, sha=sha)
        except git.GitCommandError as exc:
            try:
                self._repo.git.checkout("--ours", ".")
                self._repo.git.add(".")
                self._repo.index.commit("merge: auto-resolved conflicts")
                sha = self._repo.head.commit.hexsha
                return MergeResult(success=True, sha=sha, conflicts=["auto-resolved"])
            except git.GitCommandError:
                return MergeResult(success=False, conflicts=[str(exc)])
        finally:
            try:
                self._repo.delete_remote(remote_name)
            except Exception:
                pass

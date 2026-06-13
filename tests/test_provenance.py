"""Tests for Git-based artifact provenance tracking."""

from sandbox_science.provenance import GitRepo


def test_run_creates_git_commits(tmp_path):
    repo_path = tmp_path / "test_repo"
    repo = GitRepo()
    repo.init(repo_path)

    test_file = repo_path / "result.txt"
    test_file.write_text("experiment result")

    info = repo.commit([test_file], "initial result")
    assert info.sha
    assert len(info.sha) == 40
    assert info.message == "initial result"
    assert "result.txt" in info.files


def test_artifact_files_committed(tmp_path):
    repo_path = tmp_path / "artifacts"
    repo = GitRepo()
    repo.init(repo_path)

    files = []
    for name in ["data.csv", "model.pkl", "report.md"]:
        f = repo_path / name
        f.write_text(f"content of {name}")
        files.append(f)

    info = repo.commit(files, "add artifacts")
    assert len(info.files) == 3

    history = repo.log()
    assert len(history) == 1


def test_merge_repos(tmp_path):
    repo_a_path = tmp_path / "repo_a"
    repo_b_path = tmp_path / "repo_b"

    repo_a = GitRepo()
    repo_a.init(repo_a_path)
    (repo_a_path / "file_a.txt").write_text("from A")
    repo_a.commit([repo_a_path / "file_a.txt"], "add A")

    repo_b = GitRepo()
    repo_b.init(repo_b_path)
    (repo_b_path / "file_b.txt").write_text("from B")
    repo_b.commit([repo_b_path / "file_b.txt"], "add B")

    result = repo_a.merge(repo_b)
    assert result.success
    assert (repo_a_path / "file_b.txt").exists()


def test_commit_info_accurate(tmp_path):
    repo_path = tmp_path / "info_test"
    repo = GitRepo()
    repo.init(repo_path)

    f = repo_path / "test.py"
    f.write_text("x = 1")
    info = repo.commit([f], "test commit")

    assert info.sha
    assert info.message == "test commit"
    assert info.timestamp is not None
    assert "test.py" in info.files
    assert info.author == "Sandbox Science"

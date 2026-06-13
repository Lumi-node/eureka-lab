"""Tests for reward-hacking detection and mitigation."""

import hashlib

from sandbox_science.auditor import AuditFlag, Auditor
from sandbox_science.sandbox import ExperimentResult


def test_constant_output_detected():
    auditor = Auditor()
    same_hash = hashlib.sha256(b"same output").hexdigest()
    results = [
        ExperimentResult(
            run_id=f"run_{i}",
            success=True,
            output_hash=same_hash,
            metrics={"accuracy": 0.95},
        )
        for i in range(5)
    ]

    report = auditor.cross_validate(results)
    assert not report.consistent
    assert AuditFlag.CONSTANT_OUTPUT in report.flags


def test_duplicate_hash_detected():
    auditor = Auditor()
    results = [
        ExperimentResult(
            run_id="a", success=True, output_hash="abc123", metrics={"acc": 0.80},
        ),
        ExperimentResult(
            run_id="b", success=True, output_hash="abc123", metrics={"acc": 0.82},
        ),
        ExperimentResult(
            run_id="c", success=True, output_hash="def456", metrics={"acc": 0.79},
        ),
    ]

    report = auditor.cross_validate(results)
    assert AuditFlag.DUPLICATE_HASH in report.flags


def test_legitimate_results_pass():
    auditor = Auditor()
    results = [
        ExperimentResult(
            run_id=f"run_{i}",
            success=True,
            output_hash=hashlib.sha256(f"output_{i}".encode()).hexdigest(),
            metrics={"accuracy": 0.70 + i * 0.03},
        )
        for i in range(5)
    ]

    report = auditor.cross_validate(results)
    assert report.consistent
    assert len(report.flags) == 0


def test_cross_validation_flags_outliers():
    auditor = Auditor()
    results = [
        ExperimentResult(
            run_id=f"run_{i}",
            success=True,
            output_hash=hashlib.sha256(f"output_{i}".encode()).hexdigest(),
            metrics={"accuracy": 0.80 + i * 0.01},
        )
        for i in range(5)
    ]
    results.append(
        ExperimentResult(
            run_id="outlier",
            success=True,
            output_hash=hashlib.sha256(b"outlier").hexdigest(),
            metrics={"accuracy": 0.99},
        )
    )

    report = auditor.cross_validate(results)
    assert "outlier" in report.outlier_run_ids


def test_perfect_score_flagged():
    auditor = Auditor()
    result = ExperimentResult(
        run_id="perfect",
        success=True,
        output_hash=hashlib.sha256(b"perfect").hexdigest(),
        metrics={"accuracy": 1.0, "loss": 0.0, "f1": 1.0},
    )

    report = auditor.verify(result)
    assert not report.passed
    assert AuditFlag.PERFECT_SCORE in report.flags

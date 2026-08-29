import copy

import pytest


HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64
HASH_D = "d" * 64


@pytest.fixture
def policy_package():
    package = {
        "schema": "policylab.claim_assessment_package.v0.1",
        "assessment_id": HASH_A,
        "package_content_id": HASH_B,
        "profile": {
            "id": "policylab.energy_linked_claim.v0",
            "domain": "energy",
            "claim_kind": "energy-linked-claim",
            "unit_mapping": {
                "source_unit": "kWh",
                "claim_unit": "kWh-claim",
                "evidence_backed_rate": 1.0,
                "calculator_id": "EVIDENCE_BACKED_CAPACITY",
                "interpretation": "One admitted claim unit per eligible source kWh.",
            },
        },
        "claim": {
            "claim_id": "claim-1",
            "case_id": "case-1",
            "subject": "Example solar delivery",
            "question": "What quantity is supportable?",
            "request_mode": "MAXIMUM_SUPPORTABLE",
            "requested_quantity": None,
            "period": {
                "canonical_utc": {
                    "start": "2026-01-01T00:00:00Z",
                    "end": "2026-01-31T23:59:59Z",
                }
            },
        },
        "evidence": {
            "assurance": "L2",
            "evidence_hash": HASH_C,
            "eligible_quantity": {
                "value": 1250.0,
                "unit": "kWh",
            },
            "warnings": [
                {"code": "SOURCE_SCOPE", "detail": "Synthetic test fixture"}
            ],
        },
        "evaluations": [
            {
                "policy": {
                    "id": "policy-a",
                    "version": "1",
                    "name": "Conservative policy",
                },
                "decision_id": HASH_D,
                "external_reading": "ADMITTED_WITH_LIMIT_UNDER_POLICY",
                "supported_quantity": {
                    "value": 1000.0,
                    "unit": "kWh-claim",
                },
                "binding_calculators": ["EVIDENCE_BACKED_CAPACITY"],
                "rule_evaluations": [
                    {
                        "calculator_id": "EVIDENCE_BACKED_CAPACITY",
                        "warnings": ["Capacity binds"],
                    }
                ],
            }
        ],
        "settlement": {"scenario_only": True},
    }
    return copy.deepcopy(package)

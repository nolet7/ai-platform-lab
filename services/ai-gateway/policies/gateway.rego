package ai.gateway

import rego.v1


allowed_use_cases := {
    "avalara-tax-team": {
        "tax-compliance-assistant",
    },

    "compliance-team": {
        "tax-compliance-assistant",
        "restricted-tax-document",
    },

    "data-science-team": {
        "tax-compliance-assistant",
        "model-evaluation",
    },
}


tenant_allowed if {
    _ := allowed_use_cases[input.tenant_id]
}


use_case_allowed if {
    allowed := allowed_use_cases[input.tenant_id]
    input.use_case in allowed
}


classification_allowed if {
    input.data_classification in {
        "public",
        "internal",
    }
}


classification_allowed if {
    input.data_classification == "confidential"
    input.tenant_id in {
        "avalara-tax-team",
        "compliance-team",
    }
}


classification_allowed if {
    input.data_classification == "restricted"
    input.tenant_id == "compliance-team"
}


provider_allowed if {
    input.provider in {
        "auto",
        "mock-primary",
        "mock-secondary",
    }
}


model_allowed if {
    input.model in {
        "auto",
        "mock-primary-v1",
        "mock-secondary-v1",
    }
}


default decision := {
    "allow": false,
    "reason": "Request denied by AI platform policy",
}


decision := {
    "allow": true,
    "reason": "Tenant, use case, classification, provider, and model are authorized",
} if {
    tenant_allowed
    use_case_allowed
    classification_allowed
    provider_allowed
    model_allowed
}

# Mock Avalara tax category classifier

This is a fictional training example for the AI Platform golden path. It is
not an Avalara product, does not call Avalara APIs, and contains no Avalara,
customer, taxpayer, or production transaction data.

The sample predicts one of three demonstration labels:

- TAXABLE_TANGIBLE
- TAXABLE_SAAS
- EXEMPT_PROFESSIONAL_SERVICE

The labels simplify tax behavior for an ML demonstration and must not be used
for tax calculation, tax advice, compliance decisions, or production filing.

## Files

- src/generate_data.py creates deterministic synthetic transactions.
- src/train.py validates the dataset, trains a scikit-learn pipeline, enforces
  a macro-F1 quality gate, and registers the model in MLflow.
- tests/test_sample.py checks privacy-safe generation, schema, and inference.
- model-template.json is the proposed platform catalog entry. Add it to the
  authoritative catalog only after a model version is successfully registered.

Follow docs/mock-avalara-data-scientist-walkthrough.md from environment setup
through portal deployment.

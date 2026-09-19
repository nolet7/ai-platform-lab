# __DISPLAY_NAME__

This project was created from the AI Platform MLflow and KServe golden
template.

1. Implement load_training_data and build_and_evaluate in src/train.py.
2. Add unit, data contract, and model quality tests.
3. Train with immutable DATASET_VERSION and SOURCE_GIT_SHA values.
4. Register a Ready numeric version in the platform MLflow registry.
5. Add model-template.json (including owner and minimum macro F1) to platform/model-catalog.json in a reviewed PR.
6. After the catalog rollout, select the model and numeric version in the
   portal, submit, and obtain approval from a different identity.

The platform resolves the MLflow version to an immutable model ID, validates
run and dataset lineage, generates KServe and Crossplane GitOps resources,
and observes readiness through Argo CD and the CAIPE agents.

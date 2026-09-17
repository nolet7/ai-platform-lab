# Tax classifier serving alerts and SLO

These alerts cover the GitOps-managed `tax-document-classifier` KServe predictor in `ml-platform`. They rely on the `tax-classifier-mlserver` PodMonitor and live MLServer port 8082. The local lab objective is 99.9% monthly inference availability and p95 inference HTTP latency below 500 ms. The alert thresholds below are early warning thresholds, not proof that the objectives have been met. The synthetic sample workload is not a production quality measurement.

## TaxClassifierServingDown

**Signal:** No scrape target or no successful scrape for two minutes. Check `kubectl -n ml-platform get inferenceservice tax-document-classifier`, then predictor pod status and events. Verify the PodMonitor selector, named `metrics` container port, NetworkPolicy ingress from `observability`, and `/metrics` on port 8082. If the model fails to load, inspect storage initializer and MLServer logs; compare the GitOps model ID and S3 URI with the validated MLflow candidate. Restore the last known good immutable Git revision through the approval process if a recent release caused the outage.

## TaxClassifierHighInferenceErrorRate

**Signal:** More than 5% inference failures for five minutes. Inspect `model_infer_request_failure_total`, the corresponding success counter, and MLServer logs. Check whether failures began after a model change and whether input schema or dependency versions changed. Validate a known synthetic W-2, invoice, and receipt request with `scripts/ml-platform/verify-tax-classifier-v2.py`. Escalate to the model owner; rollback to the previous immutable model only through the approved release workflow.

## TaxClassifierHighInferenceLatency

**Signal:** p95 HTTP inference latency exceeds 500 ms for five minutes. Inspect request volume, `rest_server_request_duration_seconds_bucket`, predictor CPU and memory, and queue metrics. Look for restarts, resource throttling, and unusually large inputs. Re-run the V2 smoke test after remediation. The local objective is a lab target and should be recalibrated from real traffic before production use.

## TaxClassifierPredictorRestarted

**Signal:** At least one predictor restart in 15 minutes. Inspect `kubectl -n ml-platform describe pod` for the current predictor and recent container logs. Distinguish OOM, liveness failures, image pull failures, and model load failures. Check the GitOps ServingRuntime image and immutable model URI. If the new release is responsible, use the approved rollback path and verify V2 readiness afterward.

## Verification

After any change, confirm the PodMonitor target is `up=1` in Prometheus, the InferenceService is `Ready=True`, and all three synthetic V2 inference checks pass. Alert routing through Alertmanager and end-to-end notification delivery remain separate verification steps.

Live validation on 2026-09-17: the predictor PodMonitor target returned up=1, all four rules loaded, and the V2 health and three synthetic predictions passed after fixing KServe Service port selection. Run `scripts/ml-platform/verify-tax-classifier-monitoring.py` to repeat the scrape check.

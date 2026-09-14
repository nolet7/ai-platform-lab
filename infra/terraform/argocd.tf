locals {
  argocd_chart_version = "10.9.0"
}

resource "helm_release" "argocd" {
  name       = "argocd"
  repository = "https://argoproj.github.io/argo-helm"
  chart      = "argo-cd"
  version    = local.argocd_chart_version

  namespace        = "argocd"
  create_namespace = false

  values = [
    file("${path.module}/argocd-values.yaml")
  ]

  wait          = true
  wait_for_jobs = true
  timeout       = 600
}

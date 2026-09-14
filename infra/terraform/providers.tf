provider "kubernetes" {
  config_path    = "~/.kube/config"
  config_context = "kind-ai-platform"
}

provider "helm" {
  kubernetes = {
    config_path    = "~/.kube/config"
    config_context = "kind-ai-platform"
  }
}

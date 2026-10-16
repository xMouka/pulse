output "kubeconfig_path" {
  description = "Use with: kubectl --kubeconfig <path> get nodes"
  value       = kind_cluster.this.kubeconfig_path
}

output "namespace" {
  value = kubernetes_namespace.app.metadata[0].name
}

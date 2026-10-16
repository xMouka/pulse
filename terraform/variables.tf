variable "cluster_name" {
  description = "Name of the kind cluster"
  type        = string
  default     = "pulse"
}

variable "namespace" {
  description = "Namespace the app is deployed into"
  type        = string
  default     = "pulse"
}

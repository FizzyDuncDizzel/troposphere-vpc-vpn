# Variable definitions
variable "region" {}
variable "bucket" {
  type    = string
  default = "img-mgr-frankisthebest-commo-terraformstatebucket-976xihn8fhuo"
}
variable "ImageId" {
  type        = string
  default     = "ami-00be885d550dcee43"
  description = "AMI used by the Launch Configuration"
}
variable "ssh_key" {
  type        = string
  default     = "ssh47"
  description = "SSH Key"
}

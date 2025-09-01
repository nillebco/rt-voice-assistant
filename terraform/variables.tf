variable "hcloud_token" {
  sensitive = true
}

variable "location" {
  default = "nbg1"
}

variable "instances" {
  default = "1"
}

variable "server_type" {
  # https://www.hetzner.com/cloud/
  default = "cpx51"
}

variable "os_type" {
  default = "ubuntu-24.04"
}

variable "ssh_key_file" {
  default = "~/.ssh/id_rsa.pub"
}

variable "service_name" {
}

variable "tailscale_domain" {
}

variable "tailscale_auth_key" {
  sensitive = true
}

variable "my_ip_addresses" {
  default = ""
}

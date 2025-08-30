resource "hcloud_ssh_key" "default" {
  name       = "hetzner_key"
  public_key = file(local.ssh_key_file)
}

locals {
  ssh_key_file = endswith(var.ssh_key_file, ".pub") ? var.ssh_key_file : "${var.ssh_key_file}.pub"
}
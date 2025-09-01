resource "hcloud_firewall" "allow_ssh_from_home" {
  count = length(local.my_ip_addresses) == 0 ? 0 : 1
  name = "allow-ssh-from-home"

  rule {
    direction = "in"
    protocol  = "tcp"
    port      = "22"
    source_ips = local.my_ip_addresses
  }
}

resource "hcloud_firewall_attachment" "allow_ssh_from_home" {
  count = length(local.my_ip_addresses) == 0 ? 0 : var.instances
  firewall_id = hcloud_firewall.allow_ssh_from_home[0].id
  server_ids  = [hcloud_server.podman[count.index].id]
}

locals {
  my_ip_addresses = split(",", var.my_ip_addresses)
}
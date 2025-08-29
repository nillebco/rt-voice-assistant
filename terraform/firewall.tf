resource "hcloud_firewall" "allow_ssh_from_home" {
  count = var.my_ip_address == null ? 0 : 1
  name = "allow-ssh-from-home"

  rule {
    direction = "in"
    protocol  = "tcp"
    port      = "22"
    source_ips = [
      "${var.my_ip_address}/32"
    ]
  }
}

resource "hcloud_firewall_attachment" "allow_ssh_from_home" {
  count = var.my_ip_address == null ? 0 : var.instances
  firewall_id = hcloud_firewall.allow_ssh_from_home[0].id
  server_ids  = [hcloud_server.podman[count.index].id]
}

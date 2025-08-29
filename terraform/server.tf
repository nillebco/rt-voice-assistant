resource "hcloud_server" "podman" {
  count       = var.instances
  name        = var.instances > 1 ? "${var.service_name}-${count.index}" : var.service_name
  image       = var.os_type
  server_type = var.server_type
  location    = var.location
  ssh_keys    = [hcloud_ssh_key.default.id]
  labels = {
    type = "podman-server"
    service = var.service_name
  }
  public_net {
    ipv4_enabled = true
    ipv6_enabled = true
  }
  user_data = templatefile("user_data.yml", {
    # terraform read the content of the file at the path specified as a variable
    SSH_KEY_CONTENT = file(var.ssh_key_path)
    TAILSCALE_AUTH_KEY = var.tailscale_auth_key
    TAILSCALE_DOMAIN = var.tailscale_domain
    SERVICE_NAME = var.service_name
  })
}

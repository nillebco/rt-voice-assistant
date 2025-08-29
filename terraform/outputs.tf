output "servers_status" {
  value = {
    for server in hcloud_server.podman :
    server.name => server.status
  }
}

output "servers_ipv4" {
  value = {
    for server in hcloud_server.podman :
    server.name => server.ipv4_address
  }
}

output "servers_ipv6" {
  value = {
    for server in hcloud_server.podman :
    server.name => server.ipv6_address
  }
}

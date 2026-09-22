# IBM VM deployment

This is a Compose-based deployment target for an IBM Linux VM. It keeps the portal as the only public application service; Redis and workers remain on the internal Compose network.

## Prepare the VM

1. Install Docker Engine and the Compose plugin.
2. Clone this repository.
3. Create persistent directories:

```bash
sudo mkdir -p /opt/arkan/{data,artifacts}
sudo chown -R 1000:1000 /opt/arkan
```

4. Open only TCP 80/443 in the IBM Cloud security group and VM firewall. Do not expose Redis or worker ports publicly.

## Start the production-shaped stack

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

The portal is available on port 8080 until a TLS reverse proxy is configured. For TLS, place a certificate at `/opt/arkan/certs/fullchain.pem` and `/opt/arkan/certs/privkey.pem`, then configure the host reverse proxy using `deploy/nginx-ssl.conf`.

## Operations

```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs --tail=100 control-plane job-runner portal
```

Back up `/opt/arkan/data` and `/opt/arkan/artifacts` before upgrades. Do not commit `.env` files or certificates. Run Trivy against every built image before deployment.

This is a deployment baseline, not a production security certification. Add authentication, PostgreSQL, encrypted backups, monitoring, and service authentication before exposing customer workloads.

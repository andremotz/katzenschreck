# Katzenschreck Ansible Deployment

This Ansible playbook automates the deployment of the Katzenschreck cat detection system on Raspberry Pi devices.

## Prerequisites

- Ansible 2.9 or later
- SSH access to target Raspberry Pi devices
- Python 3.6+ on target devices

## Quick Start

1. **Update inventory** with your Raspberry Pi IP addresses:
   ```yaml
   # ansible/inventory.yml
   pi3_garden:
     ansible_host: YOUR_PI_IP_ADDRESS
   ```

2. **Configure variables** in `group_vars/raspberry_pis.yml`:
   ```yaml
   rtsp_url: "rtsp://your-camera:554/stream"
   mqtt_broker: "your-mqtt-broker.local"
   db_host: "your-database.local"
   ```

3. **Deploy the system**:
   ```bash
   cd ansible
   ansible-playbook deploy-katzenschreck.yml
   ```

## Playbook Structure

```
ansible/
├── deploy-katzenschreck.yml     # Main playbook
├── inventory.yml                # Host inventory
├── ansible.cfg                  # Ansible configuration
├── group_vars/
│   └── raspberry_pis.yml       # Group variables
└── roles/
    ├── system_setup/            # System dependencies
    ├── python_environment/      # Python environment
    ├── katzenschreck_deployment/ # Application deployment
    └── service_configuration/   # Systemd service setup
```

## Configuration

### Required Variables

- `rtsp_url`: RTSP stream URL for camera
- `mqtt_broker`: MQTT broker hostname/IP
- `db_host`: Database hostname/IP
- `db_user`: Database username
- `db_password`: Database password
- `db_name`: Database name

### Optional Variables

- `enable_docker`: Deploy with Docker (default: false)
- `backup_enabled`: Enable automatic backups (default: true)
- `log_level`: Logging level (default: INFO)
- `auto_start`: Start service automatically (default: true)

## Usage Examples

### Deploy to single Pi
```bash
ansible-playbook deploy-katzenschreck.yml -l pi3_garden
```

### Deploy with custom config
```bash
ansible-playbook deploy-katzenschreck.yml -e "rtsp_url=rtsp://192.168.1.100:554/stream"
```

### Check service status
```bash
ansible raspberry_pis -m systemd -a "name=katzenschreck"
```

### View logs
```bash
ansible raspberry_pis -m shell -a "journalctl -u katzenschreck -f"
```

## Service Management

The playbook creates a systemd service named `katzenschreck`:

```bash
# Start service
sudo systemctl start katzenschreck

# Stop service
sudo systemctl stop katzenschreck

# Restart service
sudo systemctl restart katzenschreck

# Check status
sudo systemctl status katzenschreck

# View logs
sudo journalctl -u katzenschreck -f
```

## Monitoring

- **Health checks**: Every 5 minutes via cron
- **Log rotation**: Daily rotation, 30 days retention
- **Disk monitoring**: Warnings at 90% usage
- **Service monitoring**: Automatic restart on failure

## Troubleshooting

### Check deployment status
```bash
ansible-playbook deploy-katzenschreck.yml --check
```

### Verbose output
```bash
ansible-playbook deploy-katzenschreck.yml -v
```

### Test connectivity
```bash
ansible raspberry_pis -m ping
```

### Manual service restart
```bash
ansible raspberry_pis -m systemd -a "name=katzenschreck state=restarted"
```

## Security Notes

- SSH keys are recommended over passwords
- Database credentials are stored in plain text (consider using Ansible Vault)
- Service runs as non-root user
- Log files are rotated automatically


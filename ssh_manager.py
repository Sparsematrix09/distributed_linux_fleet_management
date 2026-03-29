import paramiko
import os

class SSHManager:
    
    def __init__(self, hostname, username=None, password=None, key_path=None):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.key_path = key_path
        self.client = None
    
    def connect(self):
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            if self.key_path and os.path.exists(self.key_path):
                # Use key-based authentication
                key = paramiko.RSAKey.from_private_key_file(self.key_path)
                self.client.connect(
                    self.hostname,
                    username=self.username,
                    pkey=key,
                    timeout=30
                )
            elif self.password:
                # Use password authentication
                self.client.connect(
                    self.hostname,
                    username=self.username,
                    password=self.password,
                    timeout=30
                )
            else:
                raise Exception("No authentication method provided")
            
            return True
        except Exception as e:
            print(f"SSH connection failed to {self.hostname}: {e}")
            return False
    
    def execute_command(self, command):
        if not self.client:
            return None, "Not connected"
        
        try:
            stdin, stdout, stderr = self.client.exec_command(command)
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            return output, error
        except Exception as e:
            return None, str(e)
    
    def close(self):
        if self.client:
            self.client.close()
    
    def install_node_exporter(self):
        install_script = '''
#!/bin/bash
# Check if Node Exporter is already installed
if command -v node_exporter &> /dev/null; then
    echo "Node Exporter already installed"
    exit 0
fi

# Create user
sudo useradd --no-create-home --shell /bin/false nodeusr 2>/dev/null || true

# Download and install Node Exporter
cd /tmp
wget -q https://github.com/prometheus/node_exporter/releases/download/v1.7.0/node_exporter-1.7.0.linux-amd64.tar.gz
tar xzf node_exporter-1.7.0.linux-amd64.tar.gz
sudo mv node_exporter-1.7.0.linux-amd64/node_exporter /usr/local/bin/
sudo chown nodeusr:nodeusr /usr/local/bin/node_exporter

# Create systemd service
sudo tee /etc/systemd/system/node_exporter.service > /dev/null << 'EOF'
[Unit]
Description=Prometheus Node Exporter
After=network.target

[Service]
User=nodeusr
Group=nodeusr
Type=simple
ExecStart=/usr/local/bin/node_exporter

[Install]
WantedBy=multi-user.target
EOF

# Start Node Exporter
sudo systemctl daemon-reload
sudo systemctl enable node_exporter
sudo systemctl start node_exporter

# Clean up
rm -rf node_exporter-1.7.0.linux-amd64*

echo "Node Exporter installed and started successfully"
'''
        return self.execute_command(install_script)
    
    def reboot_node(self):
        return self.execute_command('sudo reboot')
    
    def get_node_status(self):
        output, error = self.execute_command('systemctl is-active node_exporter')
        is_running = output.strip() == 'active'
        return is_running

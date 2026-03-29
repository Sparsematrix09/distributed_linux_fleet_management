import os

class Config:
    # Database
    DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'database', 'fleet.db')
    
    # Prometheus targets file
    PROMETHEUS_TARGETS_FILE = r'C:\fleet-sim\prometheus\targets\targets.json'
    
    # Node Exporter port
    NODE_EXPORTER_PORT = 9100
    
    # SSH settings
    SSH_TIMEOUT = 30
    
    # AWS EC2 settings - CORRECTED PATH
    EC2_KEY_PATH = r'C:\fleet-sim\keys\fleet-management-key.pem'
    EC2_USERNAME = 'ubuntu'
    
    # Your AWS EC2 nodes
    AWS_NODES = [
        {'name': 'aws-node1', 'ip': '52.66.248.14', 'username': 'ubuntu', 'key_path': EC2_KEY_PATH},
        {'name': 'aws-node2', 'ip': '13.235.70.67', 'username': 'ubuntu', 'key_path': EC2_KEY_PATH},
        {'name': 'aws-node3', 'ip': '13.235.69.190', 'username': 'ubuntu', 'key_path': EC2_KEY_PATH},
    ]
    
    # Docker nodes (skip for now)
    DOCKER_NODES = [
        {'name': 'node1', 'ip': 'localhost:9101'},
        {'name': 'node2', 'ip': 'localhost:9102'},
        {'name': 'node3', 'ip': 'localhost:9103'},
    ]
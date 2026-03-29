import json
import os

class PrometheusManager:
    
    def __init__(self, targets_file):
        self.targets_file = targets_file
        self._ensure_targets_file()
    
    def _ensure_targets_file(self):
        os.makedirs(os.path.dirname(self.targets_file), exist_ok=True)
        if not os.path.exists(self.targets_file):
            self._write_targets([])
    
    def _write_targets(self, targets):
        with open(self.targets_file, 'w') as f:
            json.dump(targets, f, indent=2)
    
    def _read_targets(self):
        if os.path.exists(self.targets_file):
            with open(self.targets_file, 'r') as f:
                return json.load(f)
        return []
    
    def add_node(self, node_ip, node_port=9100):
        targets = self._read_targets()
        
        # Check if node already exists
        target_string = f"{node_ip}:{node_port}"
        if any(t['targets'][0] == target_string for t in targets):
            return False
        
        # Add new target
        targets.append({
            'targets': [target_string],
            'labels': {
                'source': 'fleet_webapp',
                'node_ip': node_ip
            }
        })
        
        self._write_targets(targets)
        return True
    
    def remove_node(self, node_ip, node_port=9100):
        targets = self._read_targets()
        target_string = f"{node_ip}:{node_port}"
        
        targets = [t for t in targets if t['targets'][0] != target_string]
        self._write_targets(targets)
        return True
    
    def list_nodes(self):
        targets = self._read_targets()
        return [t['targets'][0].split(':')[0] for t in targets]
    
    def node_exists(self, node_ip, node_port=9100):
        targets = self._read_targets()
        target_string = f"{node_ip}:{node_port}"
        return any(t['targets'][0] == target_string for t in targets)

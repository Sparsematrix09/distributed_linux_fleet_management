from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import sqlite3
import os
import subprocess
import requests
import socket
from datetime import datetime

from config import Config
from ssh_manager import SSHManager
from prometheus_manager import PrometheusManager

app = Flask(__name__)
app.secret_key = 'fleet-management-secret-key'

# Initialize managers
prometheus_manager = PrometheusManager(Config.PROMETHEUS_TARGETS_FILE)

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def log_audit(node_id, action, status, message):
    """Log audit entry"""
    conn = get_db()
    conn.execute(
        'INSERT INTO audit_log (node_id, action, status, message) VALUES (?, ?, ?, ?)',
        (node_id, action, status, message)
    )
    conn.commit()
    conn.close()

def test_node_connectivity(ip, node_type):
    try:
        # Force IPv4 + correct port
        if ':' in ip:
            host, port = ip.split(':')
        else:
            host, port = ip, 9100

        url = f"http://{host}:{port}/metrics"

        # 👇 IMPORTANT FIXES
        res = requests.get(
            url,
            timeout=5,
            headers={"Connection": "close"}
        )

        print(f"[DEBUG] {url} → {res.status_code}")

        return res.status_code == 200

    except Exception as e:
        print(f"[ERROR] {ip}: {e}")
        return False

@app.route('/')
def index():
    """Home page - show dashboard"""
    conn = get_db()
    nodes = conn.execute('SELECT * FROM nodes ORDER BY onboarded_at DESC').fetchall()
    conn.close()
    
    # Update status for each node
    for node in nodes:
        is_online = test_node_connectivity(node['ip'], node['node_type'])
        conn = get_db()
        conn.execute('UPDATE nodes SET status = ?, last_seen = ? WHERE id = ?',
                    ('online' if is_online else 'offline', datetime.now().isoformat(), node['id']))
        conn.commit()
        conn.close()
    
    # Refresh node list
    conn = get_db()
    nodes = conn.execute('SELECT * FROM nodes ORDER BY onboarded_at DESC').fetchall()
    conn.close()
    
    # Get Prometheus targets
    prometheus_nodes = prometheus_manager.list_nodes()
    
    return render_template('index.html', nodes=nodes, prometheus_nodes=prometheus_nodes)

@app.route('/nodes')
def nodes():
    """List all nodes (API)"""
    conn = get_db()
    nodes = conn.execute('SELECT id, name, ip, node_type, status, onboarded_at, last_seen FROM nodes ORDER BY onboarded_at DESC').fetchall()
    conn.close()
    return jsonify([dict(node) for node in nodes])

@app.route('/onboard', methods=['GET', 'POST'])
def onboard():
    """Onboard a new node"""
    if request.method == 'GET':
        return render_template('onboard.html')
    
    # Get form data
    node_ip = request.form.get('ip')
    node_name = request.form.get('name', node_ip)
    username = request.form.get('username')
    password = request.form.get('password')
    use_key = request.form.get('use_key') == 'on'
    
    if not all([node_ip, username]):
        flash('IP address and username are required', 'error')
        return redirect(url_for('onboard'))
    
    try:
        # Check if node already exists
        conn = get_db()
        existing = conn.execute('SELECT id FROM nodes WHERE ip = ?', (node_ip,)).fetchone()
        if existing:
            flash(f'Node {node_ip} already exists in the fleet', 'error')
            conn.close()
            return redirect(url_for('onboard'))
        
        # Establish SSH connection
        key_path = Config.EC2_KEY_PATH if use_key else None
        ssh_manager = SSHManager(node_ip, username, password, key_path)
        
        if not ssh_manager.connect():
            flash(f'SSH connection failed to {node_ip}. Check credentials and network.', 'error')
            conn.close()
            return redirect(url_for('onboard'))
        
        # Install Node Exporter
        output, error = ssh_manager.install_node_exporter()
        
        if error and 'error' in error.lower():
            flash(f'Node Exporter installation failed: {error}', 'error')
            ssh_manager.close()
            conn.close()
            return redirect(url_for('onboard'))
        
        ssh_manager.close()
        
        # Add to database
        cursor = conn.execute(
            'INSERT INTO nodes (name, ip, node_type, username, password, status) VALUES (?, ?, ?, ?, ?, ?)',
            (node_name, node_ip, 'custom', username, password if not use_key else None, 'online')
        )
        node_id = cursor.lastrowid
        conn.commit()
        
        # Add to Prometheus
        prometheus_manager.add_node(node_ip)
        
        # Log audit
        log_audit(node_id, 'onboard', 'success', f'Node {node_ip} onboarded successfully')
        
        flash(f'Node {node_ip} onboarded successfully!', 'success')
        return redirect(url_for('index'))
        
    except Exception as e:
        flash(f'Error onboarding node: {str(e)}', 'error')
        return redirect(url_for('onboard'))

@app.route('/reboot/<int:node_id>', methods=['POST'])
def reboot_node(node_id):
    """Reboot a managed node"""
    conn = get_db()
    node = conn.execute('SELECT * FROM nodes WHERE id = ?', (node_id,)).fetchone()
    conn.close()
    
    if not node:
        flash('Node not found', 'error')
        return redirect(url_for('index'))
    
    try:
        # Connect via SSH
        ssh_manager = SSHManager(node['ip'], node['username'], node['password'])
        
        if not ssh_manager.connect():
            flash(f'SSH connection failed to {node["ip"]}', 'error')
            return redirect(url_for('index'))
        
        # Execute reboot
        output, error = ssh_manager.reboot_node()
        ssh_manager.close()
        
        # Update database
        conn = get_db()
        conn.execute('UPDATE nodes SET last_reboot = ? WHERE id = ?',
                    (datetime.now().isoformat(), node_id))
        conn.commit()
        conn.close()
        
        # Log audit
        log_audit(node_id, 'reboot', 'success', f'Reboot command sent to {node["ip"]}')
        
        flash(f'Reboot command sent to {node["name"]} ({node["ip"]})', 'success')
        
    except Exception as e:
        flash(f'Error rebooting node: {str(e)}', 'error')
        log_audit(node_id, 'reboot', 'failed', str(e))
    
    return redirect(url_for('index'))

@app.route('/remove/<int:node_id>', methods=['POST'])
def remove_node(node_id):
    """Remove node from fleet"""
    conn = get_db()
    node = conn.execute('SELECT * FROM nodes WHERE id = ?', (node_id,)).fetchone()
    
    if not node:
        flash('Node not found', 'error')
        return redirect(url_for('index'))
    
    # Remove from Prometheus
    prometheus_manager.remove_node(node['ip'])
    
    # Remove from database
    conn.execute('DELETE FROM nodes WHERE id = ?', (node_id,))
    conn.commit()
    conn.close()
    
    # Log audit
    log_audit(node_id, 'remove', 'success', f'Node {node["ip"]} removed from fleet')
    
    flash(f'Node {node["name"]} ({node["ip"]}) removed from fleet', 'success')
    return redirect(url_for('index'))

@app.route('/status/<int:node_id>')
def node_status_api(node_id):
    """Get node status as JSON"""
    conn = get_db()
    node = conn.execute('SELECT * FROM nodes WHERE id = ?', (node_id,)).fetchone()
    conn.close()
    
    if not node:
        return jsonify({'error': 'Node not found'}), 404
    
    is_online = test_node_connectivity(node['ip'], node['node_type'])
    
    return jsonify({
        'id': node['id'],
        'name': node['name'],
        'ip': node['ip'],
        'status': 'online' if is_online else 'offline',
        'last_seen': node['last_seen'],
        'last_reboot': node['last_reboot']
    })

@app.route('/audit')
def audit_log():
    """View audit log"""
    conn = get_db()
    logs = conn.execute('''
        SELECT a.*, n.name as node_name, n.ip as node_ip 
        FROM audit_log a 
        LEFT JOIN nodes n ON a.node_id = n.id 
        ORDER BY a.timestamp DESC 
        LIMIT 100
    ''').fetchall()
    conn.close()
    return render_template('audit.html', logs=logs)

if __name__ == '__main__':
    # Initialize database
    from init_db import init_database
    init_database()
    
    # Add pre-configured Docker nodes to database if they don't exist
    conn = get_db()
    for docker_node in Config.DOCKER_NODES:
        existing = conn.execute('SELECT id FROM nodes WHERE ip = ?', (docker_node['ip'],)).fetchone()
        if not existing:
            conn.execute(
                'INSERT INTO nodes (name, ip, node_type, username, password, status) VALUES (?, ?, ?, ?, ?, ?)',
                (docker_node['name'], docker_node['ip'], 'docker', docker_node['username'], docker_node['password'], 'online')
            )
            prometheus_manager.add_node(docker_node['ip'])
    conn.commit()
    conn.close()
    
    print("=" * 50)
    print("Linux Fleet Management System")
    print("=" * 50)
    print(f"Web UI: http://localhost:5000")
    print(f"Prometheus: http://localhost:9090")
    print(f"Grafana: http://localhost:3000 (admin/admin)")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=5000, debug=True)

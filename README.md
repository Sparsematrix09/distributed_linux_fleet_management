Fleet Monitoring System
A full-stack infrastructure monitoring system to track the health and status of distributed nodes (AWS EC2 + Docker) in real time using Prometheus and a custom Flask dashboard.

Features
 Monitor AWS EC2 and Docker nodes
 Real-time node status (Online / Offline)
 Prometheus-based metrics collection
 Grafana dashboard visualization
 Custom Flask web UI for fleet management
 Dynamic node onboarding and removal
 Smart connectivity checks using HTTP metrics

Tech Stack
Backend: Python, Flask
Monitoring: Prometheus
Visualization: Grafana
Infrastructure: AWS EC2, Docker
Database: SQLite
Tools: Git, REST APIs

## ⚙️ Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/Sparsematrix09/fleet-monitoring-system.git
cd fleet-monitoring-system
2. Create Virtual Environment (Recommended)
py -m venv venv
venv\Scripts\activate
3. Install Dependencies
py -m pip install -r requirements.txt
4. Setup Database
py setup_db.py
py init_db.py
5. Configure Paths

Update config.py:

DATABASE_PATH
PROMETHEUS_TARGETS_FILE
EC2_KEY_PATH
6. Start Application
py app.py
7. Access Services
Web UI → http://localhost:5000
Prometheus → http://localhost:9090
Grafana → http://localhost:3000

---

# 🐳 Docker Setup (Optional)

```markdown
## 🐳 Docker Setup (Optional)

Run Node Exporter containers:

```bash
docker run -d --name node1 -p 9101:9100 node-image
docker run -d --name node2 -p 9102:9100 node-image
docker run -d --name node3 -p 9103:9100 node-image

Update Prometheus targets:

[
  { "targets": ["localhost:9101"], "labels": { "node": "node1" } },
  { "targets": ["localhost:9102"], "labels": { "node": "node2" } },
  { "targets": ["localhost:9103"], "labels": { "node": "node3" } }
]

---

# ☁️ AWS Setup

```markdown
## ☁️ AWS Setup

### 1. Launch EC2 Instances
- Use Ubuntu
- Open port **9100** in Security Group

### 2. Install Node Exporter
```bash
wget https://github.com/prometheus/node_exporter/releases/latest/download/node_exporter-*.tar.gz
tar xvf node_exporter-*.tar.gz
cd node_exporter-*
./node_exporter
3. Use Elastic IP (Recommended)
Go to EC2 → Elastic IPs
Allocate & Associate with instance
4. Update Prometheus Targets
{
  "targets": ["<ELASTIC_IP>:9100"]
}
```
<table>
  <tr>
    <td><img src="screenshots/dashboard.png" width="400"/></td>
    <td><img src="screenshots/prometheus.png" width="400"/></td>
  </tr>
  <tr>
    <td align="center">Dashboard</td>
    <td align="center">Prometheus Targets</td>
  </tr>
</table>

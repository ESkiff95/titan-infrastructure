# TITAN INFRASTRUCTURE PROTOCOL

**Status:** OPERATIONAL
**Classification:** PRIVATE / SELF-HOSTED
**Architecture:** Ansible (Push-Based)

## MISSION STATEMENT
To establish a resilient, version-controlled infrastructure ("The Vault") capable of autonomous operation. This repository contains the Infrastructure-as-Code (IaC) blueprints required to deploy, secure, and maintain the Titan Network.

---

## 1. ARCHITECTURE

### THE COMMAND CHAIN
* **Control Node:** Fedora Workstation (The Architect)
* **Protocol:** Ansible (Automation & Configuration Management)

### THE FLEET

| Node Name | Role | IP Address | OS | Mission |
| :--- | :--- | :--- | :--- | :--- |
| **TITAN (Core)** | Fortress | `192.168.1.240` | Linux | Central Compute, Databases, Document Archival (Paperless), Security Scanning (GVM). |
| **SENTRY (Edge)** | Watchtower | `192.168.1.84` | Ubuntu (Mac) | NVR (Frigate), Object Detection, Perimeter Defense. |

---

## 2. CAPABILITIES

### GLOBAL BASELINE (All Nodes)
* **Hardening:** UFW Firewall (Default Deny), Fail2Ban, SSH Key Enforcement.
* **Engine:** Docker CE with automated conflict resolution.
* **Networks:**
    * `vault_net`: Secure, isolated bridge for sensitive data.
    * `tribe_net`: Shared bridge for utility/media services.

### CORE OPERATIONS (Titan Only)
* **Paperless-ngx:** Digital archive and document OCR.
* **GVM (Greenbone):** Vulnerability scanning and threat assessment.
* **Infrastructure:** Postgres, Redis, Traefik (Reverse Proxy).

### EDGE OPERATIONS (Sentry Only)
* **Frigate NVR:** AI-powered video surveillance.
* **Optimization:** Configured with RAM Disks (`shm_size`) to preserve SSD longevity.

---

## 3. DEPLOYMENT PROTOCOL

### PREREQUISITES
1.  **Secrets:** A `inventory/group_vars/all.yml` file must exist (it is gitignored) containing:
    * `camera_user` / `camera_password`
    * `mqtt_host`
    * `gvm_db_user` / `gvm_db_password`
2.  **SSH Access:** Public keys must be deployed to all nodes.

### EXECUTION COMMANDS

**Full System Deploy (The "Nuke & Pave"):**

```bash
ansible-playbook -i inventory/hosts.ini site.yml
```

**Targeted Deploy (Surgical):**
Use tags to update specific components without touching the rest of the stack.

```bash
# Update Firewall Rules Only
ansible-playbook -i inventory/hosts.ini site.yml --tags "security"

# Update Frigate Config Only
ansible-playbook -i inventory/hosts.ini site.yml --tags "nvr"

# Run System Updates Only
ansible-playbook -i inventory/hosts.ini site.yml --tags "common"
```

---

## 4. DIRECTOQY STRUCTURE

* `inventory/`: Defines the servers and their groups.
* `roles/`: The capability modules (e.g., `frigate`, `docker`, `security`).
* `site.yml`: The Master Playbook that orchestrates the roles.
* `backups/`: (Local Only) Automated configuration pulls from the nodes.

---

## 5. SECURITY NOTICES
* **Credential Isolation:** No passwords are stored in this repository. They are injected via the `group_vars` file at runtime.
* **Port Discipline:** Only essential ports (SSH, HTTP/S, RTSP) are exposed via UFW.

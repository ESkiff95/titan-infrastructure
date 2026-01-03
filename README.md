# Titan Infrastructure Protocol

Automated deployment and hardening protocol for a tiered home lab environment.

## Architecture
* **The Brain:** Paperless-ngx & Document Management.
* **The Sentry:** Frigate NVR & Object Detection (Edge Node).
* **The Shield:** UFW & Fail2Ban Hardening.

## Usage
1.  Copy `inventory/hosts.example.ini` to `inventory/hosts.ini`.
2.  Populate with your own IPs and user credentials.
3.  Run the site playbook:
    ```bash
    ansible-playbook -i inventory/hosts.ini site.yml
    ```

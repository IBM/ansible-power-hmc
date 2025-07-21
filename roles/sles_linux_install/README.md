
# SUSE Linux Installation Role for IBM PowerVM

This Ansible role automates the process of installing SUSE LINUX on IBM PowerVM logical partitions (LPARs) using a **network-based installation via TFTP boot**.

## Overview

There are multiple ways to install SUSE on IBM Power servers. This role focuses on automating the **TFTP-based network installation** method using Ansible. It sets up the necessary infrastructure and orchestrates the installation process end-to-end.

## Required Infrastructure

To perform the installation, the following components must be configured:

1. **HTTP (Repo) Server**  
   Hosts the SUSE distribution files and serves them via HTTP. This can be a dedicated server with multiple distro builds or a simple HTTP server with the required build.

2. **PXE Server**  
   Runs both `tftpd` and `dhcpd` services. This role will configure these services if they are not already running.

3. **LPAR (Logical Partition)**  
   The target system where SUSE will be installed.

## Role Workflow

1. **PXE Server Setup**  
   - Checks for running DHCP and TFTP services.
   - If not found, configures and enables them.
   - DHCP configuration is dynamically generated based on the subnet of the target LPAR using the `dhcp_server_conf.j2` template.
   - TFTP is configured to serve files from `/var/lib/tftpboot`.

2. **Kickstart File Generation**  
   - A kickstart file is created on the HTTP server containing the installation configuration.

3. **Boot File Preparation**  
   - Required boot files are downloaded to the PXE server.
   - A GRUB configuration file is generated using the kickstart file.

4. **Network Boot Trigger**  
   - The `lpar_netboot` command is executed from the HMC to initiate a network boot on the LPAR.
   - The LPAR sends a BOOTP request to the PXE server and begins the OS installation.

## Post-Installation Validation

After installation, the role prints the OS distribution name and version installed on the LPAR to verify success.

# Dynamic Host Configuration Protocol (DHCP) and Layer 2 Security

## Overview
Dynamic Host Configuration Protocol (DHCP), defined in RFC 2131, is an application layer client-server protocol that automatically provides an Internet Protocol (IP) host with its IP address and other related configuration parameters such as the default gateway, subnet mask, and DNS server addresses.

## The DORA Lease Acquisition Process
DHCP operates over UDP using port 67 for servers and port 68 for clients. When an unconfigured host boots up on a local network segment, it acquires a lease via four primary phases:

### 1. DHCP Discover
- **Sender:** Client (Source IP: `0.0.0.0`, Source Port: `68`, Destination IP: `255.255.255.255`, Destination Port: `67`).
- **Ethernet Frame:** Broadcast MAC (`FF:FF:FF:FF:FF:FF`).
- **Purpose:** The client broadcasts its existence and requests an IP lease. The payload includes the client hardware address (MAC) and requested parameter list (Option 55).

### 2. DHCP Offer
- **Sender:** DHCP Server (Source IP: Server IP e.g. `192.168.1.1`, Destination IP: `255.255.255.255` or client unicast IP).
- **Purpose:** The server reserves an available IP from its address pool and transmits an offer packet.
- **Payload Attributes:**
  - `yiaddr` (Your IP Address): The offered IP address (e.g., `192.168.1.150`).
  - Subnet Mask: Option 1 (`255.255.255.0`).
  - Router/Default Gateway: Option 3 (`192.168.1.1`).
  - Domain Name Server: Option 6 (`1.1.1.1`, `8.8.8.8`).
  - IP Address Lease Time: Option 51 (e.g., 86400 seconds / 24 hours).

### 3. DHCP Request
- **Sender:** Client (Source IP: `0.0.0.0`, Destination IP: `255.255.255.255`).
- **Purpose:** The client selects one received offer and formally requests it. By broadcasting this request, other DHCP servers that made offers learn that their offers were declined and can return their reserved addresses back to the pool. The packet includes Option 54 (Server Identifier) indicating which server's offer was accepted.

### 4. DHCP Acknowledge (ACK)
- **Sender:** Selected DHCP Server.
- **Purpose:** The server commits the lease binding into its database and transmits a final ACK to the client. Upon receiving the ACK, the client performs Gratuitous ARP (GARP) to ensure no duplicate IP exists on the segment before binding the address.

## Lease Renewal (T1 and T2 Timers)
- **T1 Timer (Renewal):** At 50% of the lease duration, the client attempts to renew the lease by sending a unicast DHCP Request directly to the original granting server.
- **T2 Timer (Rebinding):** If no ACK is received and the lease reaches 87.5% of its total duration, the client transitions to the Rebinding state and broadcasts a DHCP Request to any reachable DHCP server.
- **Expiration:** If the full lease duration elapses without an ACK, the client must immediately release the IP address and restart the DORA cycle from DHCP Discover.

## DHCP Relay Agent (Option 82)
When DHCP clients and DHCP servers reside on separate broadcast domains or subnets, routers or Layer 3 switches act as DHCP Relay Agents (RFC 3046).
- The relay agent listens for client broadcasts on UDP port 67.
- It inserts the **Option 82** (Relay Agent Information Option) containing:
  - Agent Circuit ID (sub-option 1): Identifies the incoming physical interface or VLAN.
  - Agent Remote ID (sub-option 2): Identifies the relay agent switch/chassis identifier.
- The relay agent rewrites the packet with its own interface IP in the `giaddr` (Gateway IP Address) field and unicasts the packet to the centralized DHCP server.

## Layer 2 DHCP Attacks and Defenses

### 1. DHCP Starvation Attack
An attacker floods the network with thousands of DHCP Discover packets using randomized source MAC addresses, exhausting the DHCP server's available IP address pool.
- **Mitigation: Port Security:** Limits the maximum number of MAC addresses learned on a switch port and puts the interface into `err-disable` upon violation.

### 2. Rogue DHCP Server Attack
A malicious device acts as an unauthorized DHCP server, answering client Discovers faster than the legitimate server, handing out attacker-controlled default gateway and DNS addresses to execute Man-in-the-Middle (MitM) attacks.
- **Mitigation: DHCP Snooping:**
  - Switch ports are categorized into **Trusted** and **Untrusted** interfaces.
  - Trusted ports connect to authorized DHCP servers or uplink switches; DHCP Offer and ACK packets are permitted.
  - Untrusted ports connect to end hosts. If a DHCP Offer or ACK packet is received on an untrusted port, the switch immediately drops the packet and disables the port.
  - The switch constructs a **DHCP Snooping Binding Database** mapping: Client MAC Address $\leftrightarrow$ Leased IP Address $\leftrightarrow$ VLAN $\leftrightarrow$ Switch Port $\leftrightarrow$ Lease Time.

### 3. Dynamic ARP Inspection (DAI)
DAI leverages the DHCP Snooping Binding Database to validate Address Resolution Protocol (ARP) packets across untrusted ports, preventing ARP Poisoning and ARP Spoofing attacks.

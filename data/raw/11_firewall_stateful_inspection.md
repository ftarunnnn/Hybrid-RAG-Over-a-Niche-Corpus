# Stateful Packet Inspection, Zone-Based Firewalls, and TCP State Tracking

## Overview
A firewall is a network security device that monitors and controls incoming and outgoing network traffic based on predetermined security rules. Modern enterprise firewalls implement **Stateful Packet Inspection (SPI)** rather than relying solely on stateless packet filters.

## Stateless vs Stateful Inspection
- **Stateless Packet Filtering (ACLs):** Inspects individual packets in total isolation based strictly on Layer 3 and Layer 4 header fields (Source IP, Destination IP, Protocol, Port). Lacks awareness of connection context. To allow return traffic, administrators had to leave high-numbered ephemeral ports wide open (ports 1024–65535), creating dangerous vulnerabilities.
- **Stateful Packet Inspection (SPI):** Tracks the operating state of active network connections across Layer 3, Layer 4, and Layer 7. When an outbound connection is initiated, the firewall verifies the TCP handshake, records the flow into a dynamic **State Table**, and automatically permits returning response traffic that strictly matches the existing flow state without requiring permissive static inbound ACLs.

## The State Table Architecture
The state table records a connection's canonical 5-tuple:
$$\text{State Entry} = (\text{Source IP}, \text{Destination IP}, \text{Source Port}, \text{Destination Port}, \text{Protocol})$$
Along with connection tracking metadata:
- Expected TCP Sequence and Acknowledgment numbers.
- TCP Connection State (`SYN_SENT`, `ESTABLISHED`, `FIN_WAIT`, `TIME_WAIT`).
- Dynamic Inactivity Timeout timers (e.g., 3600 seconds for active TCP; 30 seconds for UDP flows).
- Layer 7 Application Protocol Identification (Application-ID / Next-Gen Firewall inspection).

## TCP Handshake Validation and State Tracking
A stateful firewall strictly monitors the TCP finite state machine:
1. **Outbound SYN:** Client sends SYN packet to remote server. Firewall checks security policy. If permitted, creates embryonic state table entry with status `SYN_SENT`.
2. **Inbound SYN-ACK:** Server responds with SYN-ACK. Firewall verifies that ACK number corresponds to the client sequence number stored in the state table. State advances to `SYN_RECEIVED`.
3. **Outbound ACK:** Client sends completing ACK. Firewall verifies sequence numbers and transitions connection to `ESTABLISHED`.
4. **Out-of-Order / Spoofed Segments:** If a packet arrives containing unexpected sequence numbers outside the valid sliding window or invalid flags (e.g., `XMAS` scan: FIN+PSH+URG, or `NULL` scan: no flags), the firewall drops the packet and logs an intrusion event.

## Zone-Based Policy Firewall (ZFW) Architecture
Rather than applying security rules to individual physical interfaces, modern network firewalls group interfaces into logical **Security Zones**:
- **Zone Concept:** Interfaces assigned to the same zone belong to the same security clearance. Traffic between interfaces within the same zone is permitted by default.
- **Inter-Zone Traffic:** Traffic moving between two distinct zones is completely dropped by default until explicitly permitted by a bidirectional or stateful **Zone-Pair Policy**.
- **Common Zone Topologies:**
  - `INSIDE` (Trust): Internal corporate workstations and local subnets.
  - `DMZ` (Demilitarized Zone): Public-facing servers (web, reverse proxies, mail).
  - `OUTSIDE` (Untrust): Untrusted public Internet.
- **Directional Policies:**
  - `INSIDE -> OUTSIDE`: Permit all outbound traffic statefully.
  - `INSIDE -> DMZ`: Permit specific administrative ports (SSH, SQL).
  - `OUTSIDE -> DMZ`: Permit only public service ports (TCP 80, TCP 443).
  - `OUTSIDE -> INSIDE`: Explicitly Deny All (all unsolicited inbound connections blocked).

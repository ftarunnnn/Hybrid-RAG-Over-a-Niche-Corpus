# Production Network Troubleshooting Playbook and Diagnostic Methodologies

## Structured Troubleshooting Models
When troubleshooting enterprise networks, ad-hoc guesswork causes prolonged downtime. Engineers use structured methodologies:
1. **Top-Down:** Starting at Layer 7 (Application) down to Layer 1 (Physical). Best when application errors or SSL cert issues are evident.
2. **Bottom-Up:** Starting at Layer 1 (Cabling, link lights) up to Layer 7. Best when physical changes or fiber cuts occurred.
3. **Divide-and-Conquer:** Starting at Layer 3 (Ping gateway, check routing table). If Layer 3 works, troubleshoot up (L4-L7); if Layer 3 fails, troubleshoot down (L1-L2).

## Layer-by-Layer Diagnostics

### Layer 1 & 2: Physical and Data Link Troubleshooting
Common symptoms: Interface flapping, intermittent packet loss, CRC errors.
- **Interface CRC Errors:** Indicates physical layer faults (damaged copper/fiber, bad SFP transceiver, electromagnetic interference, or duplex mismatch).
  - *Duplex Mismatch Signature:* One side is set to Half-Duplex (shows late collisions) and the other is set to Full-Duplex (shows CRC/frame alignment errors).
- **Spanning Tree Protocol (STP) Loops:**
  - Caused by unmanaged switches plugged into access ports without BPDU Guard, or unidirectional fiber link failures.
  - Signature: Switch CPU spikes to 100%, broadcast packet rates skyrocket, MAC address table flapping (`%SW_MATM-4-MACFLAP_NOTIF`).
  - Mitigations: Enable `spanning-tree portfast bpduguard enable` on all access interfaces; enable `udld aggressive` on fiber trunks.

### Layer 3: Network Layer and MTU Black Holes
- **Path MTU Discovery (PMTUD) and MTU Black Hole:**
  - Standard Ethernet MTU is 1500 bytes. When encapsulated in tunnels (IPsec, GRE, VXLAN, PPPoE), headers add 20 to 58 bytes.
  - If a packet has the `DF` (Don't Fragment) bit set and encounters a link with MTU 1450, the intermediate router drops the packet and transmits an ICMP Type 3 Code 4 message (*Destination Unreachable, Fragmentation Needed and DF Set*).
  - **The Black Hole Problem:** If an upstream firewall blocks all ICMP traffic, the sender never receives the ICMP Type 3 Code 4 message. Small TCP packets (like the 3-way handshake) pass through, but large data transfers (SSL certificate exchanges or HTTP file downloads) stall and time out indefinitely.
  - **Remediation:**
    1. Permit ICMP Type 3 Code 4 through firewalls.
    2. Clamp TCP MSS on the WAN router:
       ```text
       interface GigabitEthernet0/1
        ip tcp adjust-mss 1360
       ```

### Diagnostic CLI Commands and Interpretation
```bash
# Verify Layer 3 reachability and Round-Trip Time
ping -c 5 -s 1472 -M do 192.168.1.1
# (-s 1472 + 20 bytes IP header + 8 bytes ICMP header = 1500 bytes with DF bit)

# Trace path hops and identify latency / routing drops
traceroute -n -T -p 443 10.20.30.1
# (-T uses TCP SYN packets to bypass ICMP-blocking firewalls)

# Inspect socket states and buffer backlogs
ss -tulpn
# (Shows listening TCP/UDP sockets, process PIDs, Recv-Q, and Send-Q)

# Packet capture for deep packet analysis
tcpdump -nn -vv -i eth0 'tcp port 443 and (tcp[tcpflags] & (tcp-syn|tcp-rst) != 0)'
# (Captures all SYN and RST flags traversing port 443)
```

### TCP Reset (RST) Root Cause Analysis
When analyzing packet captures in Wireshark, sudden TCP RST flags indicate:
1. **Port Closed / No Listener:** Destination host has no process listening on the target port; the kernel immediately sends `RST, ACK`.
2. **Stateful Firewall Timeout:** Middlebox drops idle connections from its state table; next packet from either endpoint is dropped or reset.
3. **SYN Flood Defense / IPS:** Deep packet inspection appliance detects signature violation and injects spoofed TCP RST to terminate session.
4. **Asymmetric Routing:** Return packets bypass the stateful firewall that saw the initial SYN; the firewall sees return traffic with invalid sequence numbers and drops or resets.

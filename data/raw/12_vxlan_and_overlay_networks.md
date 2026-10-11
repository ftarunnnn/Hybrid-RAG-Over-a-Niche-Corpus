# Virtual Extensible LAN (VXLAN) and Data Center Overlay Networks

## Overview
Virtual Extensible LAN (VXLAN), defined in RFC 7348, is an encapsulation protocol that provides Layer 2 overlay networking over a Layer 3 underlay infrastructure. VXLAN solves the scalability limitations of traditional multi-tenant data centers, enabling virtual machine mobility across physical subnet boundaries.

## Limitations of Traditional Layer 2 Data Centers
1. **The 4096 VLAN Limit:** Traditional 802.1Q tags reserve 12 bits for the VLAN ID, capping tenant segregation at 4,094 usable VLANs. Massive cloud service providers host hundreds of thousands of isolated tenants.
2. **Spanning Tree Protocol (STP) Inefficiency:** STP prevents Layer 2 loops by blocking redundant links, leaving up to 50% of costly data center link bandwidth idle.
3. **Large MAC Address Tables:** Top-of-Rack (ToR) switches were required to learn the MAC addresses of every physical and virtual machine across the entire data center fabric.

## VXLAN Header and Encapsulation Mechanics
VXLAN encapsulates an entire inner Layer 2 Ethernet frame inside an outer Layer 4 UDP packet traversing an IP routed underlay:
- **Outer UDP Port:** Standard destination port **4789** (assigned by IANA).
- **VXLAN Network Identifier (VNI):** A **24-bit identifier** supporting up to **16,777,216 ($16\text{M}$)** distinct virtual segments, shattering the 4,096 VLAN bottleneck.
- **Outer Headers Added:**
  - Outer Ethernet Header (14 bytes)
  - Outer IP Header (20 bytes)
  - Outer UDP Header (8 bytes)
  - VXLAN Header (8 bytes, including 24-bit VNI)
  - Total Overhead: **50 bytes** (or 54 bytes if outer 802.1Q tagging is active).

### The MTU Sizing Imperative
Because the VXLAN encapsulation adds 50 bytes of overhead to an standard 1500-byte Ethernet frame, physical switches across the routed underlay network MUST be configured with **Jumbo Frames (MTU 1600 or minimum 1550 bytes)**. Failure to increase underlay MTU forces packet fragmentation or causes packet drops if the DF bit is set, breaking overlay connectivity.

## VXLAN Architecture Components
- **VTEP (VXLAN Tunnel Endpoint):** The entity responsible for originating and terminating VXLAN tunnels. A VTEP encapsulates tenant frames entering the overlay and decapsulates frames exiting to tenant workloads. VTEPs can be hardware switches (ToR ASICs) or virtual hypervisor switches (OVS / VMware NSX).
- **Underlay Network:** The physical routed network (commonly a Leaf-Spine Clos topology running eBGP or OSPF with Equal-Cost Multi-Pathing / ECMP) providing fast IP transport between VTEP IP addresses.
- **Overlay Network:** The virtual Layer 2 or Layer 3 network perceived by tenant workloads, completely isolated from physical underlay IP addressing.

## Control Plane: Multicast Flood-and-Learn vs BGP EVPN
1. **Data Plane Learning (Multicast Underlay):** Early VXLAN implementations used underlay IP multicast groups to handle Broadcast, Unknown Unicast, and Multicast (BUM) traffic and dynamic MAC learning. This introduced complex PIM-SM underlay dependencies.
2. **BGP EVPN Control Plane (RFC 7432 / RFC 8365):** Modern data centers deploy Ethernet VPN (EVPN) as a unified BGP control plane. VTEPs advertise tenant MAC and IP addresses via BGP Route Type 2 (MAC/IP Advertisement) and Route Type 3 (Inclusive Multicast Ethernet Tag), eliminating data plane flooding and providing scalable ARP suppression.

# Virtual LANs (VLANs), IEEE 802.1Q Trunking, and Inter-VLAN Routing

## Overview
A Virtual Local Area Network (VLAN) is a logical grouping of network devices within the same broadcast domain, regardless of their physical switch location. VLANs enforce Layer 2 isolation, restrict broadcast storms, enhance security boundaries, and simplify subnet administration.

## IEEE 802.1Q Frame Encapsulation
When an Ethernet frame traverses an inter-switch link carrying traffic for multiple VLANs (a **Trunk Link**), the sending switch inserts an IEEE 802.1Q tag directly into the Ethernet header between the Source MAC Address and the EtherType fields.

### 802.1Q 4-Byte Tag Structure:
1. **TPID (Tag Protocol Identifier - 16 bits):** Constant value `0x8100`, identifying the frame as an 802.1Q tagged frame.
2. **TCI (Tag Control Information - 16 bits):**
   - **PCP (Priority Code Point - 3 bits):** Implements IEEE 802.1p Quality of Service (QoS) with 8 traffic priority levels (0 for best-effort up to 7 for network control).
   - **DEI (Drop Eligible Indicator - 1 bit):** Indicates frames that may be discarded in the event of interface buffer congestion.
   - **VID (VLAN Identifier - 12 bits):** Identifies the VLAN membership ($2^{12} = 4096$ theoretical values).
     - Reserved: `0` (priority-only frame) and `4095` (reserved).
     - Standard Range: `1` to `1005` (VLAN 1 is factory default).
     - Extended Range: `1006` to `4094`.

## Trunk Ports vs Access Ports
- **Access Port:** Connects to an end device (workstation, printer, server NIC). Frames exiting an access port have their 802.1Q tags stripped by the switch ASIC; frames arriving are tagged with the port's configured Access VLAN.
- **Trunk Port:** Connects between switches or between a switch and a router/firewall. Transmits and receives tagged frames across multiple VLANs.

### The Native VLAN Concept
On an IEEE 802.1Q trunk, one VLAN is designated as the **Native VLAN** (default is VLAN 1):
- Untagged frames received on a trunk port are automatically mapped to the Native VLAN.
- Frames belonging to the Native VLAN exiting the trunk port are transmitted **untagged**.
- **Security Vulnerability: VLAN Hopping:** An attacker on an access port configured with the Native VLAN can double-tag a frame (`[Outer Tag: Native VLAN][Inner Tag: Target VLAN 20]`). The first switch strips the outer tag without inspecting further; the downstream switch receives the inner tag and forwards the frame into VLAN 20.
- **Best Practice Mitigation:** Change the Native VLAN to an unused, dummy VLAN ID (e.g., VLAN 999) and tag native VLAN traffic explicitly:
  ```bash
  vlan dot1q tag native
  ```

## Inter-VLAN Routing Architecture
Because Layer 2 switches do not forward traffic between disparate VLANs, inter-VLAN communication requires a Layer 3 routing engine:

### 1. Router-on-a-Stick (ROAS)
A single physical router interface connects to a switch trunk port. The router interface is subdivided into logical **subinterfaces**:
```text
interface GigabitEthernet0/0.10
 encapsulation dot1Q 10
 ip address 192.168.10.1 255.255.255.0
!
interface GigabitEthernet0/0.20
 encapsulation dot1Q 20
 ip address 192.168.20.1 255.255.255.0
```
- Drawback: Becomes a throughput bottleneck because traffic traversing between VLANs must travel up and down the same physical router link.

### 2. Multi-Layer Switching (Switched Virtual Interfaces - SVI)
Layer 3 enterprise switches route inter-VLAN packets at wire speed in hardware using Application-Specific Integrated Circuits (ASICs):
```text
ip routing
!
interface Vlan10
 ip address 192.168.10.1 255.255.255.0
 no shutdown
!
interface Vlan20
 ip address 192.168.20.1 255.255.255.0
 no shutdown
```

# Open Shortest Path First (OSPF): Link-State Protocol Architecture and LSA Types

## Overview
Open Shortest Path First (OSPF), defined in RFC 2328 (OSPFv2 for IPv4) and RFC 5340 (OSPFv3 for IPv6), is an open-standard Interior Gateway Protocol (IGP) based on link-state technology. Unlike distance-vector protocols (RIP, EIGRP), every OSPF router maintains an identical Link-State Database (LSDB) representing the complete network topology map and computes the Shortest Path Tree (SPT) independently using Edsger Dijkstra's Shortest Path First (SPF) algorithm.

## OSPF Hierarchical Area Design
To prevent SPF recalculation churn across massive networks, OSPF partitions autonomous systems into two-tier hierarchical areas:
- **Backbone Area (Area 0 / Area 0.0.0.0):** The central core of the OSPF domain. All non-backbone areas must connect directly to Area 0.
- **Standard Non-Backbone Areas:** Subordinate areas carrying internal routes and summary routes from the backbone.
- **Area Border Router (ABR):** A router with interfaces in both Area 0 and one or more non-backbone areas. ABRs generate Type 3 Summary LSAs.
- **Autonomous System Boundary Router (ASBR):** A router that redistributes routes from external sources (BGP, static, EIGRP) into OSPF. ASBRs generate Type 5 External LSAs.

## OSPF Neighbor Adjacency States
Neighbor discovery operates via the OSPF Hello protocol over multicast IP `224.0.0.5` (All OSPF Routers) and `224.0.0.6` (All DR Routers). Adjacency progresses through 7 states:
1. **Down:** Initial state; no Hello packets heard from the neighbor.
2. **Init:** A Hello packet was received, but the local router's Router ID does not yet appear in the neighbor's received Hello list (unidirectional communication).
3. **2-Way:** Bi-directional communication confirmed. On broadcast multi-access networks (Ethernet), the **Designated Router (DR)** and **Backup Designated Router (BDR)** election occurs. Routers not elected enter `DROTHER` state and only form full adjacencies with DR and BDR.
4. **ExStart:** First step in LSDB synchronization. Routers negotiate a Master/Slave relationship and select the Initial Sequence Number for Database Description (DBD) packets based on the highest Router ID.
5. **Exchange:** Routers exchange DBD packets containing summary headers of all LSAs in their LSDBs.
6. **Loading:** Routers compare DBD summaries with their own LSDB. If newer or missing LSAs are identified, they send Link-State Requests (LSR), answered by Link-State Updates (LSU) containing full LSA payloads, confirmed by Link-State Acknowledgments (LSAck).
7. **Full:** The Link-State Databases of both adjacent routers are 100% synchronized.

## The DR/BDR Election Mechanism
On multi-access broadcast segments, $N$ routers would require $\frac{N(N-1)}{2}$ full adjacencies, creating exponential flooding overhead. OSPF elects a single DR and one BDR:
- **Priority:** Configured via `ip ospf priority <0-255>` (Default 1). A priority of `0` permanently excludes a router from becoming DR/BDR.
- **Tie-Breaker:** Highest Router ID (explicitly configured `router-id`, or highest active loopback IP, or highest active physical IP).
- **Non-Preemptive:** If a router with higher priority boots after the election has concluded, it does **not** usurp the existing DR/BDR until the current DR/BDR reboots or fails.

## Comprehensive OSPF LSA Types
| LSA Type | Name | Originator | Flooding Scope | Content & Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **Type 1** | Router LSA | Every OSPF router | Intra-Area (stays within originating area) | Lists all active interfaces, IP subnets, link types, and link metric costs. |
| **Type 2** | Network LSA | DR of multi-access segment | Intra-Area | Advertises the subnet mask and list of all attached adjacent routers on the segment. |
| **Type 3** | Summary LSA | Area Border Router (ABR) | Inter-Area (flooded into adjacent areas) | Advertises subnets from one area into other areas (inter-area routing). |
| **Type 4** | ASBR Summary LSA | Area Border Router (ABR) | Inter-Area | Informs routers in other areas how to reach the ASBR (provides metric cost to ASBR). |
| **Type 5** | Autonomous System External LSA | ASBR | Entire OSPF Domain (except Stub areas) | Advertises external redistributed routes. Default metric type: E2 (cost does not increase across hops). |
| **Type 7** | NSSA External LSA | ASBR inside a Not-So-Stubby Area (NSSA) | Local NSSA Only | Allows external routes inside an NSSA. Converted to Type 5 by the ABR at the Area 0 boundary. |

## Metric Calculation Formula
OSPF computes path cost using reference bandwidth:
$$\text{Cost} = \frac{\text{Reference Bandwidth}}{\text{Interface Bandwidth}}$$
By default, Cisco IOS uses a reference bandwidth of $100 \text{ Mbps}$ ($10^8 \text{ bps}$):
- FastEthernet (100 Mbps): Cost = 1.
- GigabitEthernet (1000 Mbps): Cost = 1 (rounds up to minimum integer 1).
- 10-GigabitEthernet (10 Gbps): Cost = 1.

**Crucial Production Setting:** Because 100M, 1G, and 10G interfaces all resolve to Cost 1 under legacy defaults, production networks must recalibrate the reference bandwidth to at least 100 Gbps:
```text
router ospf 1
 auto-cost reference-bandwidth 100000
```

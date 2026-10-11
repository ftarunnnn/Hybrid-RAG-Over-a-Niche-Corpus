# Border Gateway Protocol (BGP-4): Path Vector Routing and Best Path Selection

## Overview
The Border Gateway Protocol (BGP), standardized in RFC 4271, is the de facto inter-domain routing protocol of the global Internet. Classified as a **path-vector routing protocol**, BGP exchanges reachability information between distinct Autonomous Systems (AS), each identified by an Autonomous System Number (ASN, 16-bit or 32-bit).

Unlike link-state protocols that focus purely on raw bandwidth metrics, BGP makes routing decisions based on network policies, contractual peering agreements, and rich path attributes.

## BGP Peering: eBGP vs iBGP
BGP operates over reliable transport via **TCP port 179**. Peers establish an explicit unicast session:
- **External BGP (eBGP):**
  - Formed between routers in **different** Autonomous Systems.
  - Default IP Time-To-Live (TTL) is set to `1` (requires peers to be directly connected, unless `ebgp-multihop` is explicitly configured).
  - Automatically prepends the local ASN to the `AS_PATH` when advertising prefixes to external peers.
- **Internal BGP (iBGP):**
  - Formed between routers within the **same** Autonomous System.
  - Default IP TTL is `255` (peers do not need to be physically adjacent; routes can be resolved across an underlying IGP like OSPF or IS-IS).
  - **iBGP Split Horizon Rule:** To prevent routing loops within an AS where AS_PATH cannot change, a route learned via iBGP is **never** re-advertised to another iBGP peer.
  - Mitigations for iBGP full-mesh scaling:
    - **Route Reflectors (RR - RFC 4456):** Allows designated server routers to reflect iBGP routes to client peers.
    - **BGP Confederations (RFC 5065):** Divides a large AS into smaller sub-autonomous systems.

## BGP Path Attributes (PA)
BGP attributes are categorized into four classes:
1. **Well-Known Mandatory:** Must be recognized by all BGP implementations and included in every UPDATE packet (`ORIGIN`, `AS_PATH`, `NEXT_HOP`).
2. **Well-Known Discretionary:** Must be recognized by all implementations, but optional in advertisements (`LOCAL_PREF`, `ATOMIC_AGGREGATE`).
3. **Optional Transitive:** May not be recognized by all implementations; if unrecognized, it must be accepted and forwarded untouched to downstream peers (`COMMUNITY`, `AGGREGATOR`).
4. **Optional Non-Transitive:** If unrecognized by a peer, the attribute is quietly discarded and not forwarded (`MULTI_EXIT_DISCRIMINATOR - MED`).

### Deep Dive: Critical Path Attributes
- **Weight (Cisco Proprietary):** Local to the router; not passed to any peer. Range: 0 to 65,535. Highest value wins (Default: 32,768 for locally originated routes, 0 for learned routes).
- **LOCAL_PREF:** Communicates preferred outbound exit path to all routers within the **same local AS**. Transmitted across iBGP only; stripped at eBGP boundaries. Default is 100. Highest value wins.
- **AS_PATH:** Sequence of AS numbers a route has traversed. Shorter AS_PATH is preferred. Also acts as BGP's loop prevention mechanism: if a router receives an update containing its own ASN in the AS_PATH, it drops the advertisement immediately.
  - *AS-Path Prepending:* An engineering technique where an AS appends its own ASN multiple times to make an inbound link look less attractive to external networks.
- **ORIGIN:** Indicates how BGP learned the prefix:
  - `IGP (i)`: Originated via network command (Highest preference).
  - `EGP (e)`: Exterior Gateway Protocol legacy (Medium preference).
  - `Incomplete (?)`: Redistributed into BGP from another source (Lowest preference).
- **MED (Multi-Exit Discriminator):** Metric sent to an external AS to influence which inbound link that external AS should use to reach prefixes in the local AS. Lower MED wins. Not transitive across multiple AS hops.

## The BGP Best Path Selection Algorithm
When multiple paths exist to the exact same prefix, BGP evaluates attributes in this rigid, deterministic order:
1. Prefer highest **Weight** (local router only).
2. Prefer highest **LOCAL_PREF** (AS-wide).
3. Prefer locally originated routes (`network` command over `redistribution`).
4. Prefer shortest **AS_PATH** length (ignoring AS_SET).
5. Prefer lowest **ORIGIN** code (`IGP < EGP < Incomplete`).
6. Prefer lowest **MED** (compared only among routes from the same neighboring AS, unless `bgp always-compare-med` is enabled).
7. Prefer **eBGP paths over iBGP paths**.
8. Prefer lowest IGP metric to the BGP **NEXT_HOP** address.
9. If BGP Multipath is enabled, install up to $k$ equal-cost paths in the RIB.
10. Prefer route with lowest **BGP Router ID** (BGP RID).
11. Prefer route with shortest **Cluster List** (in Route Reflector topologies).
12. Prefer neighbor with lowest **IP address**.

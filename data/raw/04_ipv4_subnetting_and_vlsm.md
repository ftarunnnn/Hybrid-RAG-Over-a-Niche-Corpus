# IPv4 Subnetting, Variable Length Subnet Masking (VLSM), and CIDR

## Overview
IPv4 addresses are 32-bit identifiers represented as four decimal octets separated by periods (e.g., `192.0.2.1`). Subnetting divides a larger network into smaller, isolated broadcast domains to preserve address space, enhance routing efficiency, and isolate security zones.

## Classful vs Classless Inter-Domain Routing (CIDR)
Prior to RFC 1519 (1993), IP addresses followed rigid class boundaries:
- **Class A:** `1.0.0.0` to `126.0.0.0` (Default Mask `/8` or `255.0.0.0`, 16,777,214 hosts per network).
- **Class B:** `128.0.0.0` to `191.255.0.0` (Default Mask `/16` or `255.255.0.0`, 65,534 hosts per network).
- **Class C:** `192.0.0.0` to `223.255.255.0` (Default Mask `/24` or `255.255.255.0`, 254 hosts per network).
- **Class D:** `224.0.0.0` to `239.255.255.255` (Multicast).
- **Class E:** `240.0.0.0` to `255.255.255.255` (Experimental / Reserved).

**CIDR notation** replaced classful boundaries by appending a slash followed by the prefix length ($/n$), representing the number of contiguous leading 1-bits in the subnet mask.

## Subnetting Mathematical Mechanics
Given a subnet mask with $n$ prefix bits:
- **Host Bits ($h$):** $h = 32 - n$.
- **Total IP Addresses:** $2^h$.
- **Usable Host Addresses:** $2^h - 2$ (The first address is the **Network Identifier**; the final address is the **Directed Broadcast Address**).
- **Block Size (Magic Number):** In the significant octet, $\text{Block Size} = 256 - \text{Octet Subnet Mask Value}$.

### Common IPv4 Subnet Reference Table
| CIDR | Subnet Mask | Total IPs | Usable Hosts | Use Case |
| :--- | :--- | :--- | :--- | :--- |
| `/24` | `255.255.255.0` | 256 | 254 | Standard user LAN |
| `/25` | `255.255.255.128` | 128 | 126 | Split department subnet |
| `/26` | `255.255.255.192` | 64 | 62 | Server farm tier |
| `/27` | `255.255.255.224` | 32 | 30 | Branch office |
| `/28` | `255.255.255.240` | 16 | 14 | Small DMZ |
| `/29` | `255.255.255.248` | 8 | 6 | High Availability firewall cluster |
| `/30` | `255.255.255.252` | 4 | 2 | Legacy point-to-point router link |
| `/31` | `255.255.255.254` | 2 | 2 (RFC 3021) | Modern point-to-point links (no broadcast) |
| `/32` | `255.255.255.255` | 1 | 1 | Router Loopback interface / Host route |

## Variable Length Subnet Masking (VLSM)
VLSM allows network architects to use multiple subnet masks across the same overall address block, allocating subnets tailored precisely to host counts without wasting address space.

### VLSM Design Example
Given parent block `10.10.0.0/22` (1024 total addresses):
1. **Engineering Department (Requires 450 hosts):**
   - Need $2^h - 2 \ge 450 \implies h = 9$ bits ($2^9 - 2 = 510$).
   - Prefix length: $32 - 9 = /23$.
   - Assigned Subnet: `10.10.0.0/23` (Range: `10.10.0.1` – `10.10.1.254`, Broadcast: `10.10.1.255`).
2. **Sales Department (Requires 120 hosts):**
   - Need $2^h - 2 \ge 120 \implies h = 7$ bits ($2^7 - 2 = 126$).
   - Prefix length: $32 - 7 = /25$.
   - Assigned Subnet: `10.10.2.0/25` (Range: `10.10.2.1` – `10.10.2.126`, Broadcast: `10.10.2.127`).
3. **Point-to-Point WAN Links (Requires 2 hosts each):**
   - Prefix length: `/30` (4 IPs, 2 hosts) or `/31` (RFC 3021).
   - Link 1: `10.10.2.128/30` (`10.10.2.129` and `10.10.2.130`).
   - Link 2: `10.10.2.132/30` (`10.10.2.133` and `10.10.2.134`).

## RFC 1918 Private IPv4 Address Allocations
To mitigate global IPv4 address exhaustion prior to IPv6 adoption, RFC 1918 reserved three non-routable private ranges:
- **24-bit block (`10.0.0.0/8`):** `10.0.0.0` – `10.255.255.255` (1 Class A network, 16.7M hosts).
- **20-bit block (`172.16.0.0/12`):** `172.16.0.0` – `172.31.255.255` (16 contiguous Class B networks, 1M hosts).
- **16-bit block (`192.168.0.0/16`):** `192.168.0.0` – `192.168.255.255` (256 contiguous Class C networks, 65K hosts).

These addresses are dropped by default at Internet service provider boundary routers and require Network Address Translation (NAT) / Port Address Translation (PAT) for public Internet transit.

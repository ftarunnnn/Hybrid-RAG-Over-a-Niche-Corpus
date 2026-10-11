# Domain Name System (DNS) Architecture and Resolution

## Overview
The Domain Name System (DNS) is a hierarchical and decentralized naming system for computers, services, and other resources connected to the Internet or a private network. It translates human-friendly domain names (such as `api.internal.corp`) into numerical Internet Protocol (IP) addresses (such as `192.0.2.53` or `2001:db8::53`), which are required for locating and identifying computer services with underlying network protocols.

## Hierarchical Namespace
The DNS namespace is organized as an inverted tree structure:
1. **Root Zone (`.`):** The apex of the hierarchy, managed by IANA and operated across 13 root server IP identities (letters A through M).
2. **Top-Level Domains (TLD):** Includes generic TLDs (`.com`, `.org`, `.net`) and country-code TLDs (`.uk`, `.de`, `.jp`), maintained by authoritative registries.
3. **Second-Level Domains (SLD):** Domains registered by organizations or individuals (e.g., `cisco.com`, `kernel.org`).
4. **Subdomains:** Delegated branches within an organization (e.g., `us-east.edge.cisco.com`).

## The Recursive Resolution Workflow
When a client application (e.g., a web browser) needs to resolve a fully qualified domain name (FQDN), it queries a DNS stub resolver:
1. **Stub Resolver Query:** The client checks its local cache (`/etc/hosts`, OS resolver cache). If not cached, it sends an iterative/recursive query to the configured DNS Recursive Resolver (e.g., `1.1.1.1` or `8.8.8.8` over UDP port 53).
2. **Root Server Query:** If the recursive resolver does not have the record cached, it queries one of the root nameservers with a request for the TLD authoritative nameservers.
3. **TLD Nameserver Query:** The root server returns a referral (NS record) pointing to the TLD nameservers (e.g., `.com` nameservers). The resolver queries the TLD server.
4. **Authoritative Nameserver Query:** The TLD server provides a referral to the authoritative nameservers responsible for the specific SLD.
5. **Answer Delivery:** The authoritative nameserver responds with the requested Resource Record (e.g., A or AAAA record). The recursive resolver caches this record for the duration specified in the Time-To-Live (TTL) field and returns the answer to the client.

## Core DNS Record Types
The DNS system defines standardized resource records in RFC 1035:
- **A Record:** Maps an IPv4 address to a hostname (32-bit address, e.g., `10.20.30.40`).
- **AAAA Record:** Maps an IPv6 address to a hostname (128-bit address, e.g., `2001:0db8:85a3::8a2e:0370:7334`).
- **CNAME (Canonical Name):** Creates an alias from one domain name to another canonical domain name. Crucially, a CNAME record cannot coexist with other records for the exact same node name.
- **MX (Mail Exchange):** Directs email to mail exchange servers for the domain, with integer priority values where lower numbers indicate higher preference.
- **TXT (Text):** Carries arbitrary human or machine-readable text; commonly used for security frameworks including SPF (Sender Policy Framework), DKIM (DomainKeys Identified Mail), and DMARC.
- **PTR (Pointer):** Resolves IP addresses back to domain names in reverse lookup zones (`in-addr.arpa` for IPv4 and `ip6.arpa` for IPv6).
- **SOA (Start of Authority):** Contains administrative metadata about the zone, including primary master server, admin email, zone serial number, refresh intervals, retry timers, and negative caching TTL.

## Transport Protocol Considerations
DNS operates primarily over **UDP port 53** for low-latency queries and responses under 512 bytes (or under 4096 bytes when Extension Mechanisms for DNS / EDNS0 are enabled via RFC 6891). 
DNS falls back to **TCP port 53** when:
- The response message exceeds the maximum transmission unit or EDNS buffer size, indicated by the Truncation (`TC`) bit set in the DNS header.
- Performing authoritative Zone Transfers (AXFR/IXFR) between primary and secondary nameservers.
- Utilizing encrypted transport layers such as DNS-over-TLS (DoT, TCP port 853) or DNS-over-HTTPS (DoH, TCP port 443).

## DNS Security Extensions (DNSSEC)
DNSSEC protects against DNS spoofing and cache poisoning (such as Kaminsky attacks) by attaching cryptographic digital signatures to DNS records:
- **RRSIG (Resource Record Signature):** Holds the digital signature for a record set.
- **DNSKEY:** Contains the public key used to verify RRSIG records (Zone Signing Key - ZSK, and Key Signing Key - KSK).
- **DS (Delegation Signer):** Placed in the parent zone containing a cryptographic hash of the child zone's KSK, forming an unbroken Chain of Trust up to the root zone anchor.
- **NSEC / NSEC3:** Provides authenticated denial of existence, proving that a queried domain name does not exist without disclosing the entire zone contents.

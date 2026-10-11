"""
Generate comprehensive evaluation question-answer dataset for networking corpus.
Includes:
- Keyword-heavy questions (testing exact matches like TCP/443, RFC numbers, CLI syntax)
- Semantic/Conceptual questions (testing paraphrased intents)
- Multi-hop & comparative questions (testing hybrid fusion & reranking)
- Edge case & unanswerable questions (testing model abstention)
"""
import json
import os

eval_data = [
    # DNS Questions
    {
        "id": "QA-DNS-01",
        "question": "What is the difference between an A record and an AAAA record in DNS?",
        "topic": "DNS",
        "query_type": "keyword",
        "golden_doc_id": "01_dns_architecture_and_resolution",
        "golden_section": "Core DNS Record Types",
        "expected_answer": "An A record maps an IPv4 address (32-bit, e.g., 10.20.30.40) to a hostname, whereas an AAAA record maps an IPv6 address (128-bit) to a hostname.",
        "must_contain": ["A record", "AAAA record", "IPv4", "IPv6", "32-bit", "128-bit"]
    },
    {
        "id": "QA-DNS-02",
        "question": "Under what conditions does DNS fall back from UDP port 53 to TCP port 53?",
        "topic": "DNS",
        "query_type": "semantic",
        "golden_doc_id": "01_dns_architecture_and_resolution",
        "golden_section": "Transport Protocol Considerations",
        "expected_answer": "DNS falls back to TCP port 53 when the response message exceeds the MTU/EDNS buffer size (indicated by the Truncation TC bit set), during authoritative Zone Transfers (AXFR/IXFR), or when utilizing encrypted transports like DoT or DoH.",
        "must_contain": ["TCP port 53", "Truncation", "TC bit", "Zone Transfer", "AXFR"]
    },
    {
        "id": "QA-DNS-03",
        "question": "How does DNSSEC establish a chain of trust and authenticate that a domain does not exist?",
        "topic": "DNS",
        "query_type": "conceptual",
        "golden_doc_id": "01_dns_architecture_and_resolution",
        "golden_section": "DNS Security Extensions (DNSSEC)",
        "expected_answer": "DNSSEC uses DS records in the parent zone hashing the child KSK to build an unbroken Chain of Trust, and uses NSEC or NSEC3 records to provide authenticated denial of existence without zone walking.",
        "must_contain": ["DNSSEC", "DS record", "Chain of Trust", "NSEC", "NSEC3"]
    },
    {
        "id": "QA-DNS-04",
        "question": "Can a CNAME record coexist with an MX record for the same hostname node in DNS?",
        "topic": "DNS",
        "query_type": "keyword",
        "golden_doc_id": "01_dns_architecture_and_resolution",
        "golden_section": "Core DNS Record Types",
        "expected_answer": "No. A CNAME record cannot coexist with any other record for the exact same node name according to RFC 1035.",
        "must_contain": ["CNAME", "cannot coexist"]
    },
    
    # DHCP Questions
    {
        "id": "QA-DHCP-01",
        "question": "Explain the four steps in the DHCP DORA process and their default source and destination IP addresses.",
        "topic": "DHCP",
        "query_type": "conceptual",
        "golden_doc_id": "02_dhcp_dora_and_security",
        "golden_section": "The DORA Lease Acquisition Process",
        "expected_answer": "The four steps are Discover (client 0.0.0.0 to broadcast 255.255.255.255), Offer (server to client broadcast/unicast with yiaddr), Request (client broadcast requesting accepted offer), and ACK (server committing lease).",
        "must_contain": ["Discover", "Offer", "Request", "ACK", "0.0.0.0", "255.255.255.255"]
    },
    {
        "id": "QA-DHCP-02",
        "question": "At what lease milestones do the T1 and T2 timers trigger in DHCP?",
        "topic": "DHCP",
        "query_type": "keyword",
        "golden_doc_id": "02_dhcp_dora_and_security",
        "golden_section": "Lease Renewal (T1 and T2 Timers)",
        "expected_answer": "The T1 timer triggers renewal at 50% of the lease duration via unicast Request. The T2 timer triggers rebinding at 87.5% of total lease duration via broadcast Request.",
        "must_contain": ["T1", "50%", "T2", "87.5%"]
    },
    {
        "id": "QA-DHCP-03",
        "question": "How does DHCP Snooping prevent rogue DHCP server attacks?",
        "topic": "DHCP",
        "query_type": "semantic",
        "golden_doc_id": "02_dhcp_dora_and_security",
        "golden_section": "Layer 2 DHCP Attacks and Defenses",
        "expected_answer": "DHCP Snooping designates switch ports as Trusted or Untrusted. Untrusted ports connected to hosts drop any DHCP Offer or ACK packets, and the switch constructs a DHCP Snooping Binding Database.",
        "must_contain": ["DHCP Snooping", "Trusted", "Untrusted", "Offer", "ACK"]
    },
    {
        "id": "QA-DHCP-04",
        "question": "What is the function of DHCP Option 82 and what sub-options does it provide?",
        "topic": "DHCP",
        "query_type": "keyword",
        "golden_doc_id": "02_dhcp_dora_and_security",
        "golden_section": "DHCP Relay Agent (Option 82)",
        "expected_answer": "Option 82 is inserted by DHCP Relay Agents across subnets, providing Agent Circuit ID (sub-option 1, interface/VLAN) and Agent Remote ID (sub-option 2, switch chassis identity).",
        "must_contain": ["Option 82", "Circuit ID", "Remote ID", "Relay Agent"]
    },

    # TCP Questions
    {
        "id": "QA-TCP-01",
        "question": "Describe the TCP 3-way handshake sequence numbers and flags exchanged during connection setup.",
        "topic": "TCP/IP",
        "query_type": "conceptual",
        "golden_doc_id": "03_tcp_flow_control_and_handshake",
        "golden_section": "The 3-Way Handshake (Connection Establishment)",
        "expected_answer": "1. Client sends SYN with ISN_client. 2. Server responds with SYN-ACK, ISN_server, and Ack = ISN_client + 1. 3. Client sends ACK with Ack = ISN_server + 1.",
        "must_contain": ["SYN", "SYN-ACK", "ACK", "Initial Sequence Numbers", "ISN"]
    },
    {
        "id": "QA-TCP-02",
        "question": "Why does the active closer in a TCP connection enter the TIME-WAIT state for 2MSL?",
        "topic": "TCP/IP",
        "query_type": "semantic",
        "golden_doc_id": "03_tcp_flow_control_and_handshake",
        "golden_section": "Purpose of the TIME-WAIT State (2MSL Timer)",
        "expected_answer": "TIME-WAIT persists for 2MSL to ensure final ACK delivery (allowing retransmission of FIN if ACK was dropped) and to suppress stale duplicate packets from colliding with a new connection on the same 4-tuple.",
        "must_contain": ["TIME-WAIT", "2MSL", "final ACK", "duplicate"]
    },
    {
        "id": "QA-TCP-03",
        "question": "What is the distinction between flow control and congestion control in TCP?",
        "topic": "TCP/IP",
        "query_type": "conceptual",
        "golden_doc_id": "03_tcp_flow_control_and_handshake",
        "golden_section": "Flow Control vs Congestion Control",
        "expected_answer": "Flow control protects the receiver memory buffers using rwnd advertised in the TCP header, while congestion control protects intermediate network infrastructure from saturation using cwnd. Effective window = min(cwnd, rwnd).",
        "must_contain": ["flow control", "congestion control", "rwnd", "cwnd", "receiver"]
    },
    {
        "id": "QA-TCP-04",
        "question": "How does Google BBR differ from loss-based congestion control algorithms like Reno and Cubic?",
        "topic": "TCP/IP",
        "query_type": "conceptual",
        "golden_doc_id": "03_tcp_flow_control_and_handshake",
        "golden_section": "Modern Algorithms: Reno vs Cubic vs BBR",
        "expected_answer": "BBR measures actual Bottleneck Bandwidth (BtlBw) and minimum RTT (RTprop) rather than treating packet loss as an indicator of congestion, eliminating bufferbloat.",
        "must_contain": ["BBR", "Bottleneck Bandwidth", "RTprop", "bufferbloat", "packet loss"]
    },

    # Subnetting & CIDR Questions
    {
        "id": "QA-SUB-01",
        "question": "How many usable host addresses are available in a /26 IPv4 subnet, and what is its subnet mask?",
        "topic": "Subnetting",
        "query_type": "keyword",
        "golden_doc_id": "04_ipv4_subnetting_and_vlsm",
        "golden_section": "Subnetting Mathematical Mechanics",
        "expected_answer": "A /26 subnet has a mask of 255.255.255.192. It has 64 total IP addresses and 62 usable host addresses (2^6 - 2).",
        "must_contain": ["255.255.255.192", "62 usable", "64 total"]
    },
    {
        "id": "QA-SUB-02",
        "question": "What are the three private IPv4 address blocks allocated under RFC 1918?",
        "topic": "Subnetting",
        "query_type": "keyword",
        "golden_doc_id": "04_ipv4_subnetting_and_vlsm",
        "golden_section": "RFC 1918 Private IPv4 Address Allocations",
        "expected_answer": "The three RFC 1918 blocks are 10.0.0.0/8 (Class A, 24-bit block), 172.16.0.0/12 (Class B, 20-bit block), and 192.168.0.0/16 (Class C, 16-bit block).",
        "must_contain": ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16", "RFC 1918"]
    },
    {
        "id": "QA-SUB-03",
        "question": "Why is an RFC 3021 /31 subnet permitted on point-to-point links despite having only 2 IP addresses?",
        "topic": "Subnetting",
        "query_type": "semantic",
        "golden_doc_id": "04_ipv4_subnetting_and_vlsm",
        "golden_section": "Common IPv4 Subnet Reference Table",
        "expected_answer": "RFC 3021 permits /31 for point-to-point links because directed broadcast and network identifier addresses are unnecessary on strictly two-endpoint links, allowing both addresses to be assigned to host interfaces.",
        "must_contain": ["RFC 3021", "/31", "point-to-point", "2 hosts"]
    },

    # VLAN & 802.1Q Questions
    {
        "id": "QA-VLAN-01",
        "question": "What is the structure and byte size of an IEEE 802.1Q VLAN tag?",
        "topic": "VLANs",
        "query_type": "keyword",
        "golden_doc_id": "05_vlan_trunking_and_802_1q",
        "golden_section": "802.1Q 4-Byte Tag Structure",
        "expected_answer": "An 802.1Q tag is 4 bytes (32 bits) in length, consisting of TPID (16 bits, 0x8100) and TCI (16 bits), which includes PCP (3 bits QoS), DEI (1 bit drop eligibility), and VID (12 bits VLAN ID).",
        "must_contain": ["4 bytes", "TPID", "0x8100", "PCP", "DEI", "VID", "12 bits"]
    },
    {
        "id": "QA-VLAN-02",
        "question": "What is the Native VLAN and what security hazard is associated with it on 802.1Q trunks?",
        "topic": "VLANs",
        "query_type": "semantic",
        "golden_doc_id": "05_vlan_trunking_and_802_1q",
        "golden_section": "The Native VLAN Concept",
        "expected_answer": "The Native VLAN transports untagged frames over an 802.1Q trunk. If an attacker's access port shares the native VLAN, they can perform double-tagging VLAN hopping attacks.",
        "must_contain": ["Native VLAN", "untagged", "VLAN Hopping", "double-tagging"]
    },
    {
        "id": "QA-VLAN-03",
        "question": "Compare Router-on-a-Stick (ROAS) with Layer 3 Switched Virtual Interfaces (SVIs) for inter-VLAN routing.",
        "topic": "VLANs",
        "query_type": "conceptual",
        "golden_doc_id": "05_vlan_trunking_and_802_1q",
        "golden_section": "Inter-VLAN Routing Architecture",
        "expected_answer": "ROAS routes traffic through router subinterfaces over a single physical link creating a bottleneck, whereas Layer 3 switch SVIs route inter-VLAN traffic in hardware at wire speed using ASICs.",
        "must_contain": ["Router-on-a-Stick", "SVI", "subinterfaces", "wire speed", "ASICs"]
    },

    # OSPF Questions
    {
        "id": "QA-OSPF-01",
        "question": "List OSPF LSA Types 1, 2, 3, 4, and 5 and their respective flooding scopes and originators.",
        "topic": "Routing",
        "query_type": "conceptual",
        "golden_doc_id": "06_ospf_link_state_routing",
        "golden_section": "Comprehensive OSPF LSA Types",
        "expected_answer": "Type 1 (Router LSA, all routers, intra-area), Type 2 (Network LSA, DR, intra-area), Type 3 (Summary LSA, ABR, inter-area), Type 4 (ASBR Summary, ABR, inter-area), Type 5 (External LSA, ASBR, autonomous system domain).",
        "must_contain": ["Type 1", "Type 2", "Type 3", "Type 4", "Type 5", "ABR", "ASBR"]
    },
    {
        "id": "QA-OSPF-02",
        "question": "What multicast IP addresses are used by OSPF for Hello packets and DR communication?",
        "topic": "Routing",
        "query_type": "keyword",
        "golden_doc_id": "06_ospf_link_state_routing",
        "golden_section": "OSPF Neighbor Adjacency States",
        "expected_answer": "224.0.0.5 is used by All OSPF Routers, and 224.0.0.6 is used by All DR/BDR Routers.",
        "must_contain": ["224.0.0.5", "224.0.0.6", "DR"]
    },
    {
        "id": "QA-OSPF-03",
        "question": "Why is 'auto-cost reference-bandwidth 100000' recommended on high-speed OSPF networks?",
        "topic": "Routing",
        "query_type": "semantic",
        "golden_doc_id": "06_ospf_link_state_routing",
        "golden_section": "Metric Calculation Formula",
        "expected_answer": "The default reference bandwidth is 100 Mbps, which assigns cost 1 to 100M, 1G, and 10G interfaces alike. Recalibrating reference bandwidth to 100 Gbps differentiates high-speed interface costs.",
        "must_contain": ["reference-bandwidth", "100 Mbps", "Cost 1", "10 Gbps"]
    },

    # BGP Questions
    {
        "id": "QA-BGP-01",
        "question": "What is the BGP best path selection tie-breaking order for Weight, Local Preference, AS-Path, and MED?",
        "topic": "Routing",
        "query_type": "conceptual",
        "golden_doc_id": "07_bgp_path_vector_and_attributes",
        "golden_section": "The BGP Best Path Selection Algorithm",
        "expected_answer": "BGP prefers: 1. Highest Weight, 2. Highest LOCAL_PREF, 3. Locally originated routes, 4. Shortest AS_PATH, 5. Lowest ORIGIN code, 6. Lowest MED.",
        "must_contain": ["Weight", "LOCAL_PREF", "AS_PATH", "ORIGIN", "MED"]
    },
    {
        "id": "QA-BGP-02",
        "question": "Explain the iBGP split-horizon rule and how Route Reflectors solve its scalability issue.",
        "topic": "Routing",
        "query_type": "semantic",
        "golden_doc_id": "07_bgp_path_vector_and_attributes",
        "golden_section": "BGP Peering: eBGP vs iBGP",
        "expected_answer": "Under the iBGP split horizon rule, a route learned via iBGP is never re-advertised to another iBGP peer to prevent loops. Route Reflectors allow designated servers to reflect iBGP routes without requiring a full mesh.",
        "must_contain": ["split horizon", "iBGP", "Route Reflectors", "full mesh"]
    },
    {
        "id": "QA-BGP-03",
        "question": "What transport protocol and port does BGP utilize for neighbor peering?",
        "topic": "Routing",
        "query_type": "keyword",
        "golden_doc_id": "07_bgp_path_vector_and_attributes",
        "golden_section": "BGP Peering: eBGP vs iBGP",
        "expected_answer": "BGP utilizes TCP port 179 for unicast peering sessions.",
        "must_contain": ["TCP port 179", "TCP"]
    },

    # Troubleshooting Questions
    {
        "id": "QA-TRB-01",
        "question": "What causes an MTU Black Hole and how does TCP MSS clamping remediate it?",
        "topic": "Troubleshooting",
        "query_type": "conceptual",
        "golden_doc_id": "08_network_troubleshooting_playbook",
        "golden_section": "Layer 3: Network Layer and MTU Black Holes",
        "expected_answer": "An MTU black hole occurs when a packet with the DF bit set exceeds a link MTU, but the router ICMP Type 3 Code 4 message is blocked by a firewall. Clamping TCP MSS (e.g. 'ip tcp adjust-mss') prevents packets from exceeding the link size.",
        "must_contain": ["MTU Black Hole", "DF bit", "ICMP Type 3 Code 4", "adjust-mss", "clamping"]
    },
    {
        "id": "QA-TRB-02",
        "question": "What causes CRC errors versus late collisions on an Ethernet switch interface?",
        "topic": "Troubleshooting",
        "query_type": "semantic",
        "golden_doc_id": "08_network_troubleshooting_playbook",
        "golden_section": "Layer 1 & 2: Physical and Data Link Troubleshooting",
        "expected_answer": "Late collisions occur on the half-duplex side of a duplex mismatch, while CRC errors indicate damaged cabling, bad transceivers, noise, or the full-duplex side of a duplex mismatch.",
        "must_contain": ["duplex mismatch", "CRC errors", "late collisions", "Half-Duplex"]
    },
    {
        "id": "QA-TRB-03",
        "question": "What Wireshark command filter captures all TCP SYN and RST flags traversing port 443?",
        "topic": "Troubleshooting",
        "query_type": "keyword",
        "golden_doc_id": "08_network_troubleshooting_playbook",
        "golden_section": "Diagnostic CLI Commands and Interpretation",
        "expected_answer": "tcpdump -nn -vv -i eth0 'tcp port 443 and (tcp[tcpflags] & (tcp-syn|tcp-rst) != 0)'",
        "must_contain": ["tcp port 443", "tcp-syn|tcp-rst"]
    },

    # HTTP & TLS 1.3 Questions
    {
        "id": "QA-TLS-01",
        "question": "How does HTTP/3 with QUIC eliminate Transport-Layer Head-of-Line (HoL) blocking?",
        "topic": "Application Layer & TLS",
        "query_type": "conceptual",
        "golden_doc_id": "09_http_https_and_tls13",
        "golden_section": "Protocol Evolution from HTTP/1.1 to HTTP/3",
        "expected_answer": "QUIC runs over UDP port 443 instead of TCP. Because packet loss on one stream affects only that stream, other streams continue uninterrupted without stalling the entire connection buffer.",
        "must_contain": ["QUIC", "UDP port 443", "Head-of-Line", "stream"]
    },
    {
        "id": "QA-TLS-02",
        "question": "Why does TLS 1.3 mandate Perfect Forward Secrecy and remove static RSA key exchange?",
        "topic": "Application Layer & TLS",
        "query_type": "semantic",
        "golden_doc_id": "09_http_https_and_tls13",
        "golden_section": "TLS 1.3 Cryptographic Handshake Architecture",
        "expected_answer": "TLS 1.3 mandates ephemeral Diffie-Hellman (ECDHE/DHE) key exchange so that even if the server private key is compromised in the future, past recorded sessions cannot be retroactively decrypted.",
        "must_contain": ["Perfect Forward Secrecy", "ephemeral", "RSA", "private key"]
    },
    {
        "id": "QA-TLS-03",
        "question": "How many round trips are required for a standard full handshake in TLS 1.3 compared to TLS 1.2?",
        "topic": "Application Layer & TLS",
        "query_type": "keyword",
        "golden_doc_id": "09_http_https_and_tls13",
        "golden_section": "TLS 1.3 Cryptographic Handshake Architecture",
        "expected_answer": "TLS 1.3 requires 1 RTT for a full handshake, reduced from 2 RTTs required in TLS 1.2.",
        "must_contain": ["1-RTT", "2 Round Trips", "TLS 1.3", "TLS 1.2"]
    },

    # Cisco IOS Questions
    {
        "id": "QA-CSC-01",
        "question": "How do you configure Port Address Translation (NAT Overload) on Cisco IOS?",
        "topic": "Configuration",
        "query_type": "keyword",
        "golden_doc_id": "10_cisco_ios_configuration_manual",
        "golden_section": "4. ACCESS CONTROL LISTS (ACL) AND PAT (NAT OVERLOAD)",
        "expected_answer": "Using the command: 'ip nat inside source list <ACL_NAME> interface <OUTSIDE_INTERFACE> overload' with 'ip nat inside' on internal interfaces and 'ip nat outside' on internet interfaces.",
        "must_contain": ["ip nat inside source list", "overload", "ip nat outside"]
    },
    {
        "id": "QA-CSC-02",
        "question": "What Cisco command protects access ports from rogue switches sending BPDUs?",
        "topic": "Configuration",
        "query_type": "keyword",
        "golden_doc_id": "10_cisco_ios_configuration_manual",
        "golden_section": "2. INTERFACE, 802.1Q TRUNKING, AND SVI CONFIGURATION",
        "expected_answer": "'spanning-tree bpduguard enable' combined with 'spanning-tree portfast'.",
        "must_contain": ["spanning-tree bpduguard enable", "portfast"]
    },

    # Firewall Questions
    {
        "id": "QA-FW-01",
        "question": "What fields comprise the canonical 5-tuple tracked in a stateful firewall state table?",
        "topic": "Security",
        "query_type": "keyword",
        "golden_doc_id": "11_firewall_stateful_inspection",
        "golden_section": "The State Table Architecture",
        "expected_answer": "The canonical 5-tuple consists of Source IP, Destination IP, Source Port, Destination Port, and Protocol.",
        "must_contain": ["Source IP", "Destination IP", "Source Port", "Destination Port", "Protocol"]
    },
    {
        "id": "QA-FW-02",
        "question": "How does a Zone-Based Policy Firewall handle traffic between interfaces in the same zone vs different zones?",
        "topic": "Security",
        "query_type": "conceptual",
        "golden_doc_id": "11_firewall_stateful_inspection",
        "golden_section": "Zone-Based Policy Firewall (ZFW) Architecture",
        "expected_answer": "Traffic between interfaces in the same zone is permitted by default, while traffic between different zones is dropped by default until explicitly permitted by a zone-pair policy.",
        "must_contain": ["same zone", "permitted by default", "dropped by default", "zone-pair"]
    },

    # VXLAN Questions
    {
        "id": "QA-VX-01",
        "question": "How many virtual segments are supported by the 24-bit VNI in VXLAN compared to traditional 802.1Q VLANs?",
        "topic": "Data Center",
        "query_type": "keyword",
        "golden_doc_id": "12_vxlan_and_overlay_networks",
        "golden_section": "VXLAN Header and Encapsulation Mechanics",
        "expected_answer": "The 24-bit VNI supports up to 16,777,216 (16 million) segments, compared to the 4,096 VLAN limit in 802.1Q.",
        "must_contain": ["16,777,216", "16M", "4096", "24-bit VNI"]
    },
    {
        "id": "QA-VX-02",
        "question": "Why must the underlay network MTU be configured to at least 1550 or 1600 bytes for VXLAN?",
        "topic": "Data Center",
        "query_type": "semantic",
        "golden_doc_id": "12_vxlan_and_overlay_networks",
        "golden_section": "The MTU Sizing Imperative",
        "expected_answer": "VXLAN outer encapsulation (outer Ethernet, IP, UDP, and VXLAN headers) adds 50 bytes of overhead to inner 1500-byte frames, requiring at least 1550 bytes (Jumbo frames) to prevent fragmentation.",
        "must_contain": ["50 bytes", "overhead", "Jumbo Frames", "1550", "fragmentation"]
    },
    {
        "id": "QA-VX-03",
        "question": "What outer UDP destination port is assigned by IANA for VXLAN encapsulated packets?",
        "topic": "Data Center",
        "query_type": "keyword",
        "golden_doc_id": "12_vxlan_and_overlay_networks",
        "golden_section": "VXLAN Header and Encapsulation Mechanics",
        "expected_answer": "UDP port 4789 is the standard outer destination port assigned by IANA.",
        "must_contain": ["4789", "UDP"]
    },

    # RFC 5681 PDF Questions
    {
        "id": "QA-PDF-01",
        "question": "What four congestion control algorithms are specified in RFC 5681?",
        "topic": "TCP/IP",
        "query_type": "keyword",
        "golden_doc_id": "13_tcp_congestion_control_spec",
        "golden_section": "Section 1: The Four Algorithms",
        "expected_answer": "Slow start, congestion avoidance, fast retransmit, and fast recovery.",
        "must_contain": ["slow start", "congestion avoidance", "fast retransmit", "fast recovery"]
    },
    {
        "id": "QA-PDF-02",
        "question": "How many duplicate ACKs trigger Fast Retransmit according to RFC 5681?",
        "topic": "TCP/IP",
        "query_type": "keyword",
        "golden_doc_id": "13_tcp_congestion_control_spec",
        "golden_section": "Section 1: The Four Algorithms",
        "expected_answer": "Three duplicate ACKs trigger Fast Retransmit without waiting for the retransmission timer to expire.",
        "must_contain": ["three duplicate ACKs", "Fast Retransmit", "RTO"]
    },

    # Abstention / Unanswerable Questions (For testing grounding and preventing hallucination)
    {
        "id": "QA-UNS-01",
        "question": "What are the recommended fertilizer types for growing hydroponic tomatoes in winter?",
        "topic": "Out-of-Scope",
        "query_type": "unanswerable",
        "golden_doc_id": None,
        "golden_section": None,
        "expected_answer": "I do not have sufficient evidence in the networking corpus to answer this question.",
        "must_contain": ["insufficient evidence"]
    },
    {
        "id": "QA-UNS-02",
        "question": "How do you configure an Apache Cassandra database cluster replication strategy?",
        "topic": "Out-of-Scope",
        "query_type": "unanswerable",
        "golden_doc_id": None,
        "golden_section": None,
        "expected_answer": "I do not have sufficient evidence in the networking corpus to answer this question.",
        "must_contain": ["insufficient evidence"]
    }
]

os.makedirs("data", exist_ok=True)
eval_path = "data/eval_qa.json"
with open(eval_path, "w", encoding="utf-8") as f:
    json.dump({"benchmark_version": "1.0.0", "total_questions": len(eval_data), "questions": eval_data}, f, indent=2)

print(f"Generated {len(eval_data)} benchmark questions into {eval_path}.")

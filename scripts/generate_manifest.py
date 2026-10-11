"""
Generate corpus manifest with SHA-256 and metadata for Phase 01.
"""
import os
import hashlib
import json

raw_dir = "data/raw"
docs_meta = {
    "01_dns_architecture_and_resolution.md": {
        "title": "Domain Name System Architecture and Resolution",
        "topic": "DNS",
        "source_url": "https://datatracker.ietf.org/doc/html/rfc1035",
        "version": "RFC 1035 / RFC 6891",
        "doc_type": "markdown",
        "license": "IETF Open Standards"
    },
    "02_dhcp_dora_and_security.md": {
        "title": "Dynamic Host Configuration Protocol (DHCP) and Layer 2 Security",
        "topic": "DHCP",
        "source_url": "https://datatracker.ietf.org/doc/html/rfc2131",
        "version": "RFC 2131 / RFC 3046",
        "doc_type": "markdown",
        "license": "IETF Open Standards"
    },
    "03_tcp_flow_control_and_handshake.md": {
        "title": "Transmission Control Protocol (TCP): Flow Control and State Machine",
        "topic": "TCP/IP",
        "source_url": "https://datatracker.ietf.org/doc/html/rfc9293",
        "version": "RFC 9293 / RFC 5681",
        "doc_type": "markdown",
        "license": "IETF Open Standards"
    },
    "04_ipv4_subnetting_and_vlsm.md": {
        "title": "IPv4 Subnetting, Variable Length Subnet Masking (VLSM), and CIDR",
        "topic": "Subnetting",
        "source_url": "https://datatracker.ietf.org/doc/html/rfc1519",
        "version": "RFC 1519 / RFC 1918",
        "doc_type": "markdown",
        "license": "IETF Open Standards"
    },
    "05_vlan_trunking_and_802_1q.md": {
        "title": "Virtual LANs (VLANs), IEEE 802.1Q Trunking, and Inter-VLAN Routing",
        "topic": "VLANs",
        "source_url": "https://standards.ieee.org/ieee/802.1Q/6844/",
        "version": "IEEE 802.1Q-2022",
        "doc_type": "markdown",
        "license": "IEEE Standards Open Reference"
    },
    "06_ospf_link_state_routing.md": {
        "title": "Open Shortest Path First (OSPF): Link-State Protocol Architecture",
        "topic": "Routing",
        "source_url": "https://datatracker.ietf.org/doc/html/rfc2328",
        "version": "RFC 2328 (OSPFv2)",
        "doc_type": "markdown",
        "license": "IETF Open Standards"
    },
    "07_bgp_path_vector_and_attributes.md": {
        "title": "Border Gateway Protocol (BGP-4): Path Vector Routing and Best Path Selection",
        "topic": "Routing",
        "source_url": "https://datatracker.ietf.org/doc/html/rfc4271",
        "version": "RFC 4271",
        "doc_type": "markdown",
        "license": "IETF Open Standards"
    },
    "08_network_troubleshooting_playbook.md": {
        "title": "Production Network Troubleshooting Playbook and Diagnostic Methodologies",
        "topic": "Troubleshooting",
        "source_url": "https://wiki.wireshark.org/Troubleshooting",
        "version": "Ops Playbook 2026",
        "doc_type": "markdown",
        "license": "Internal Technical Playbook"
    },
    "09_http_https_and_tls13.html": {
        "title": "HTTP Evolution and TLS 1.3 Cryptographic Handshake Protocol",
        "topic": "Application Layer & TLS",
        "source_url": "https://datatracker.ietf.org/doc/html/rfc8446",
        "version": "RFC 8446 / RFC 9114",
        "doc_type": "html",
        "license": "IETF Open Standards"
    },
    "10_cisco_ios_configuration_manual.txt": {
        "title": "Cisco IOS Enterprise Router and Switch CLI Configuration Manual",
        "topic": "Configuration",
        "source_url": "https://www.cisco.com/c/en/us/support/ios-nx-os-software/index.html",
        "version": "Cisco IOS-XE 17.9.4a",
        "doc_type": "text",
        "license": "Engineering Operations Manual"
    },
    "11_firewall_stateful_inspection.md": {
        "title": "Stateful Packet Inspection, Zone-Based Firewalls, and TCP State Tracking",
        "topic": "Security",
        "source_url": "https://csrc.nist.gov/publications/detail/sp/800-41/rev-1/final",
        "version": "NIST SP 800-41 Rev 1",
        "doc_type": "markdown",
        "license": "Public Domain NIST Guideline"
    },
    "12_vxlan_and_overlay_networks.md": {
        "title": "Virtual Extensible LAN (VXLAN) and Data Center Overlay Networks",
        "topic": "Data Center",
        "source_url": "https://datatracker.ietf.org/doc/html/rfc7348",
        "version": "RFC 7348 / RFC 8365",
        "doc_type": "markdown",
        "license": "IETF Open Standards"
    },
    "13_tcp_congestion_control_spec.pdf": {
        "title": "TCP Congestion Control Specification (RFC 5681)",
        "topic": "TCP/IP",
        "source_url": "https://datatracker.ietf.org/doc/html/rfc5681",
        "version": "RFC 5681",
        "doc_type": "pdf",
        "license": "IETF Open Standards"
    }
}

manifest = {
    "corpus_name": "Computer Networking Knowledge Corpus",
    "version": "1.0.0",
    "total_documents": len(docs_meta),
    "documents": []
}

for filename, meta in docs_meta.items():
    filepath = os.path.join(raw_dir, filename)
    with open(filepath, "rb") as f:
        content = f.read()
    sha = hashlib.sha256(content).hexdigest()
    doc_entry = {
        "doc_id": filename.split(".")[0],
        "filename": filename,
        "filepath": filepath.replace("\\", "/"),
        "size_bytes": len(content),
        "sha256": sha,
        **meta
    }
    manifest["documents"].append(doc_entry)

os.makedirs("data", exist_ok=True)
manifest_path = "data/corpus_manifest.json"
with open(manifest_path, "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2)

print(f"Manifest written successfully to {manifest_path} with {len(manifest['documents'])} documents.")

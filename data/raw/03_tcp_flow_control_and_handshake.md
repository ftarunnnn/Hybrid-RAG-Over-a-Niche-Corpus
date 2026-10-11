# Transmission Control Protocol (TCP): Flow Control, Congestion Control, and State Machine

## Overview
The Transmission Control Protocol (TCP), formalized in RFC 793 and updated through RFC 9293, is a connection-oriented, reliable, byte-stream transport layer protocol. TCP guarantees in-order delivery, error detection, duplicate packet suppression, and end-to-end flow and congestion regulation.

## TCP Connection Lifecycle

### The 3-Way Handshake (Connection Establishment)
Before application data can traverse the connection, both endpoints synchronize their Initial Sequence Numbers (ISN):
1. **SYN (Synchronize):**
   - Client sends a TCP packet with `SYN=1`, `ACK=0`.
   - Sequence Number: $ISN_{client}$ (e.g., $1000$).
   - Flags & Options: Maximum Segment Size (MSS, e.g., 1460 bytes), Window Scale (WScale), SACK-Permitted, Timestamp option.
   - State transition: Client transitions from `CLOSED` to `SYN-SENT`.
2. **SYN-ACK (Synchronize-Acknowledge):**
   - Server responds with `SYN=1`, `ACK=1`.
   - Sequence Number: $ISN_{server}$ (e.g., $5000$).
   - Acknowledgment Number: $ISN_{client} + 1$ ($1001$).
   - State transition: Server transitions from `LISTEN` to `SYN-RECEIVED`.
3. **ACK (Acknowledge):**
   - Client replies with `SYN=0`, `ACK=1`.
   - Sequence Number: $1001$.
   - Acknowledgment Number: $ISN_{server} + 1$ ($5001$).
   - State transition: Both endpoints enter `ESTABLISHED`. Data payload can now be transmitted.

### The 4-Way Handshake (Graceful Connection Teardown)
TCP connections are full-duplex; each transmission direction must be terminated independently:
1. **FIN from Initiator:** Host A sends `FIN=1, ACK=1` ($Seq=U, Ack=V$) and enters `FIN-WAIT-1`.
2. **ACK from Receiver:** Host B responds with `ACK=1` ($Ack=U+1$) and enters `CLOSE-WAIT`. Host A enters `FIN-WAIT-2`. (Host B can continue sending pending data).
3. **FIN from Receiver:** Host B finishes sending remaining buffers and sends `FIN=1, ACK=1` ($Seq=W, Ack=U+1$) and enters `LAST-ACK`.
4. **ACK from Initiator:** Host A responds with `ACK=1` ($Ack=W+1$) and enters the **`TIME-WAIT`** state. Host B receives ACK and enters `CLOSED`.

### Purpose of the `TIME-WAIT` State (2MSL Timer)
The endpoint that initiates the active close must remain in the `TIME-WAIT` state for two times the Maximum Segment Lifetime ($2 \times MSL$, typically 60 to 120 seconds):
- **Guaranteed ACK Delivery:** Ensures that if the final ACK is dropped in transit, the retransmitted FIN from Host B can be answered.
- **Old Duplicate Suppression:** Prevents stale segments delayed in network buffers from interfering with a subsequent new connection reusing the same 4-tuple (`Source IP`, `Source Port`, `Destination IP`, `Destination Port`).

## Flow Control vs Congestion Control

### Flow Control (Receiver Window - `rwnd`)
Flow control protects the **receiver's memory buffers** from being overrun by a fast sender:
- The receiver advertises its available buffer space in the 16-bit **Window Size** header field.
- **Window Scaling (RFC 7323):** Expands the 16-bit window (max 64 KB) up to $2^{30}$ bytes (1 GB) by applying a logarithmic scale factor negotiated during the SYN handshake.
- **Zero Window Probe:** When `rwnd = 0`, the sender halts data transmission and periodically sends 1-byte probe segments to trigger window update advertisements.
- **Silly Window Syndrome:** Avoided using Clark's algorithm on the receiver (do not advertise small windows) and Nagle's algorithm on the sender (coalesce small packets into full MSS segments).

### Congestion Control (Congestion Window - `cwnd`)
Congestion control protects the **intermediate network infrastructure (routers, switches, links)** from saturation.
The maximum inflight data is bounded by:
$$\text{Effective Window} = \min(\text{cwnd}, \text{rwnd})$$

### Congestion Control Phases:
1. **Slow Start:**
   - Starts with initial window ($IW = 10 \text{ MSS}$).
   - For every ACK received, $cwnd$ increases by 1 MSS (exponential growth per Round-Trip Time: $cwnd = 2 \times cwnd$).
   - Continues until $cwnd$ reaches the Slow Start Threshold ($ssthresh$).
2. **Congestion Avoidance:**
   - Once $cwnd \ge ssthresh$, $cwnd$ grows linearly (Additive Increase: $+1 \text{ MSS}$ per RTT).
3. **Fast Retransmit & Fast Recovery (RFC 5681):**
   - Triggered upon receiving **3 Duplicate ACKs** (indicating an out-of-order gap without waiting for the RTO timeout).
   - Sender immediately retransmits the missing segment.
   - Sets $ssthresh = \max(\text{FlightSize} / 2, 2 \text{ MSS})$.
   - Sets $cwnd = ssthresh + 3 \text{ MSS}$ (Fast Recovery), avoiding a complete fallback to Slow Start.
4. **Timeout (Retransmission Timeout - RTO):**
   - Occurs when severe congestion drops all segments and ACKs.
   - Drastic penalty: $ssthresh = \text{FlightSize} / 2$, $cwnd = 1 \text{ MSS}$, RTO timer doubles (exponential backoff / Karn's algorithm), and slow start restarts.

## Modern Algorithms: Reno vs Cubic vs BBR
- **TCP Reno:** Loss-based, sawtooth AIMD (Additive Increase Multiplicative Decrease).
- **TCP Cubic:** Default in Linux; window growth governed by a cubic function of elapsed time since the last packet drop, scaling efficiently across high Bandwidth-Delay Product (BDP) links.
- **BBR (Bottleneck Bandwidth and RTT):** Model-based algorithm created by Google. BBR does not interpret packet loss as an immediate sign of congestion; instead, it measures actual Bottleneck Bandwidth ($BtlBw$) and minimum Round Trip Time ($RTprop$) to operate at Kleinrock's optimal operating point, eliminating bufferbloat.

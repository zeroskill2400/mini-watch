from scapy.all import IP, TCP, UDP
from learning.support import read_capture, capture_summary
from learning.checks import traffic_exceeded
packets = read_capture("normal.pcap")
first = packets[0]
print("패킷 수", len(packets))
print(first[IP].src, "->", first[IP].dst)
print(first[TCP].sport, "->", first[TCP].dport)
for packet in packets:
    if TCP in packet:
        print("TCP", len(bytes(packet)))
    elif UDP in packet:
        print("UDP", len(bytes(packet)))
normal = capture_summary("normal.pcap")
observed = capture_summary("observed.pcap")
print(normal)
print(observed)
print("기준 초과", traffic_exceeded(normal, observed))

from scapy.all import *
import socket
import struct

TARGET_PORT = 8022
LOOPBACK_INTERFACE = r"\Device\NPF_Loopback"

SACN_PORT = 5568  # Standard sACN Port
SACN_UNIVERSE = 1  # Universe (1–63999)

# Mapping wie von dir angegeben
dmx_mapping = {i: ((i + 32) % 256) for i in range(224)}
for i in range(224, 256):
    dmx_mapping[i] = i - 224

# UDP Socket für sACN
sacn_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def create_sacn_packet(dmx_data, universe=SACN_UNIVERSE):
    """Erstellt ein minimales sACN (E1.31) Paket"""

    # Root Layer
    preamble_size = struct.pack(">H", 0x0010)
    postamble_size = struct.pack(">H", 0x0000)
    acn_pid = b"ASC-E1.17\x00\x00\x00"

    # Framing Layer
    source_name = b"Python sACN Sender".ljust(64, b'\x00')
    priority = struct.pack("B", 100)
    sequence_number = struct.pack("B", 0)
    options = struct.pack("B", 0)
    universe_bytes = struct.pack(">H", universe)

    # DMP Layer
    vector = struct.pack("B", 0x02)
    address_type = struct.pack("B", 0xa1)
    first_property = struct.pack(">H", 0x0000)
    address_increment = struct.pack(">H", 0x0001)
    property_value_count = struct.pack(">H", len(dmx_data) + 1)

    dmx_start_code = b'\x00'
    dmx_payload = dmx_start_code + bytes(dmx_data)

    # DMP Layer zusammenbauen
    dmp_pdu = (
        b'\x70\x00' +                # Flags + Length (dummy, reicht oft)
        vector +
        address_type +
        first_property +
        address_increment +
        property_value_count +
        dmx_payload
    )

    # Framing Layer
    framing_pdu = (
        b'\x70\x00' +                # Flags + Length
        b'\x00\x00\x00\x02' +        # Vector
        source_name +
        priority +
        b'\x00\x00' +                # Sync Address
        sequence_number +
        options +
        universe_bytes +
        dmp_pdu
    )

    # Root Layer
    root_pdu = (
        b'\x70\x00' +                # Flags + Length
        b'\x00\x00\x00\x04' +        # Vector
        b'\x00' * 16 +               # CID (kann beliebig sein)
        framing_pdu
    )

    packet = preamble_size + postamble_size + acn_pid + root_pdu
    return packet


def extract_dmx(packet):
    if UDP in packet and packet[UDP].dport == TARGET_PORT:
        payload = bytes(packet[UDP].payload)
        if len(payload) > 2:
            start_index = 2  # 06 00 überspringen
            dmx_data = payload[start_index:]
            decoded = []
            for byte in dmx_data:
                for k, v in dmx_mapping.items():
                    if v == byte:
                        decoded.append(k)
                        break

            sacn_packet = create_sacn_packet(decoded)
            sacn_socket.sendto(sacn_packet, ('127.0.0.1', SACN_PORT))


print(f"Starting sniffer on {LOOPBACK_INTERFACE} Port {TARGET_PORT} and sending sACN on 127.0.0.1:{SACN_PORT}")
print("Leave this Window open! You can minimize it if you want to.")
sniff(iface=LOOPBACK_INTERFACE, filter=f"udp port {TARGET_PORT}", prn=extract_dmx)
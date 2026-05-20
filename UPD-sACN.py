from scapy.all import *
import socket
import struct
import obsws_python as obs

TARGET_PORT = 8022
LOOPBACK_INTERFACE = r"\Device\NPF_Loopback"

SACN_PORT = 5568
SACN_UNIVERSE = 1

# OBS WebSocket
OBS_HOST = "169.254.251.179"
OBS_PORT = 4455
OBS_PASSWORD = "TechnikPDS"

# OBS Client
obs_client = obs.ReqClient(
    host=OBS_HOST,
    port=OBS_PORT,
    password=OBS_PASSWORD
)

# Letzte getriggerte Scene merken
last_scene_value = 0

# Mapping wie von dir angegeben
dmx_mapping = {i: ((i + 32) % 256) for i in range(224)}
for i in range(224, 256):
    dmx_mapping[i] = i - 224

# UDP Socket für sACN
sacn_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def create_sacn_packet(dmx_data, universe=SACN_UNIVERSE):
    """Erstellt ein minimales sACN (E1.31) Paket"""

    preamble_size = struct.pack(">H", 0x0010)
    postamble_size = struct.pack(">H", 0x0000)
    acn_pid = b"ASC-E1.17\x00\x00\x00"

    source_name = b"Python sACN Sender".ljust(64, b'\x00')
    priority = struct.pack("B", 100)
    sequence_number = struct.pack("B", 0)
    options = struct.pack("B", 0)
    universe_bytes = struct.pack(">H", universe)

    vector = struct.pack("B", 0x02)
    address_type = struct.pack("B", 0xa1)
    first_property = struct.pack(">H", 0x0000)
    address_increment = struct.pack(">H", 0x0001)
    property_value_count = struct.pack(">H", len(dmx_data) + 1)

    dmx_start_code = b'\x00'
    dmx_payload = dmx_start_code + bytes(dmx_data)

    dmp_pdu = (
        b'\x70\x00' +
        vector +
        address_type +
        first_property +
        address_increment +
        property_value_count +
        dmx_payload
    )

    framing_pdu = (
        b'\x70\x00' +
        b'\x00\x00\x00\x02' +
        source_name +
        priority +
        b'\x00\x00' +
        sequence_number +
        options +
        universe_bytes +
        dmp_pdu
    )

    root_pdu = (
        b'\x70\x00' +
        b'\x00\x00\x00\x04' +
        b'\x00' * 16 +
        framing_pdu
    )

    packet = preamble_size + postamble_size + acn_pid + root_pdu
    return packet

def trigger_obs_scene(scene_value):
    """Triggert OBS Scene 0-255"""

    global last_scene_value

    # Nur reagieren wenn sich der Wert geändert hat
    if scene_value == last_scene_value:
        return

    # Neuen Wert speichern
    last_scene_value = scene_value

    scene_name = str(scene_value)

    try:
        obs_client.set_current_program_scene(scene_name)
        print(f"Triggered OBS Scene: {scene_name}")

    except Exception as e:
        print(f"OBS Scene Fehler ({scene_name}): {e}")


def extract_dmx(packet):
    if UDP in packet and packet[UDP].dport == TARGET_PORT:

        payload = bytes(packet[UDP].payload)

        if len(payload) > 2:

            start_index = 2
            dmx_data = payload[start_index:]

            decoded = []

            for byte in dmx_data:
                for k, v in dmx_mapping.items():
                    if v == byte:
                        decoded.append(k)
                        break

            # sACN weiterhin senden
            sacn_packet = create_sacn_packet(decoded)
            sacn_socket.sendto(
                sacn_packet,
                ('127.0.0.1', SACN_PORT)
            )

            # Letzten Kanal für OBS nutzen
            if len(decoded) > 0:
                last_channel_value = decoded[-1]
                trigger_obs_scene(last_channel_value)


print(f"Starting sniffer on {LOOPBACK_INTERFACE} Port {TARGET_PORT}")
print(f"Sending sACN on 127.0.0.1:{SACN_PORT}")
print("OBS Scene Trigger aktiv")
print("Leave this Window open!")

sniff(
    iface=LOOPBACK_INTERFACE,
    filter=f"udp port {TARGET_PORT}",
    prn=extract_dmx
)
import struct
from snap7.client import Client

#Configurações 
PLC_IP   = "192.168.0.1"   # Alterar para a IP do CLP
PLC_RACK = 0                # Verificar no TIA Portal > Device Configuration
PLC_SLOT = 2                # Verificar no TIA Portal > Device Configuration

DB_NUMERO   = 3           # Número do Global DB no TIA Portal
INTERVALO_S = 120           # PLC leva ~120s para preencher os arrays

# Mapeamento dos vetores no DB (sequenciais, tipo REAL = 4 bytes cada)
# Vetor 1: índices 0–1599   → bytes 0     a 6399
# Vetor 2: índices 0–1599   → bytes 6400  a 12799
# Vetor 3: índices 0–1599   → bytes 12800 a 19199

VETORES = {
    "Vetor 1": {"offset": 14,     "tamanho": 1599},
    "Vetor 2": {"offset": 6414,  "tamanho": 1599},
    "Vetor 3": {"offset": 12814, "tamanho": 1599},
}

#Cliente global
plc = Client()


def conectar_plc() -> bool:
    try:
        plc.connect(PLC_IP, PLC_RACK, PLC_SLOT)
        return plc.get_connected()
    except Exception as e:
        print(f"[PLC] Erro ao conectar: {e}")
        return False


def desconectar_plc():
    try:
        if plc.get_connected():
            plc.disconnect()
    except Exception as e:
        print(f"[PLC] Erro ao desconectar: {e}")


def esta_conectado() -> bool:
    try:
        return plc.get_connected()
    except Exception:
        return False


def ler_bloco(offset_bytes: int, tamanho: int, chunk: int = 50) -> list[float]:
    tamanho_bytes = tamanho * 4
    chunk_bytes   = chunk * 4
    raw           = bytearray()

    for pos in range(0, tamanho_bytes, chunk_bytes):
        leitura = min(chunk_bytes, tamanho_bytes - pos)
        raw.extend(plc.db_read(DB_NUMERO, offset_bytes + pos, leitura))

    n = len(raw) // 4
    return list(struct.unpack_from(f">{n}f", raw))


def ler_vetores() -> dict[str, list[float]]:
    resultado = {}
    for nome, cfg in VETORES.items():
        print(f"[PLC] Lendo {nome} (offset={cfg['offset']}, {cfg['tamanho']} REALs)...")
        resultado[nome] = ler_bloco(cfg["offset"], cfg["tamanho"])
    return resultado
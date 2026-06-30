import struct
from snap7.client import Client

# Mapeamento dos vetores no DB (sequenciais, tipo REAL = 4 bytes cada)
# Vetor 1: índices 0–1599   → bytes 0     a 6399
# Vetor 2: índices 0–1599   → bytes 6400  a 12799
# Vetor 3: índices 0–1599   → bytes 12800 a 19199

class PLCConfig:
    def __init__(self, ip="192.168.0.1", rack=0, slot=1, db=3):
        self.ip = ip
        self.rack = rack
        self.slot = slot
        self.db = db
        self.intervalo_s = 120  # PLC leva ~120s para preencher os arrays

    def atualizar(self, ip, rack, slot, db=None):
        self.ip = ip
        self.rack = rack
        self.slot = slot
        if db is not None:
            self.db = db

#Cliente global
config = PLCConfig()
plc = Client()

VETORES = {
    "Vetor 1": {"offset": 14,  "tamanho": 1600},
    "Vetor 2": {"offset": 6414,  "tamanho": 1600},
    "Vetor 3": {"offset": 12814, "tamanho": 1600},
}

def conectar_plc() -> bool:
    try:
        plc.connect(config.ip, config.rack, config.slot)
        return plc.get_connected()
    except Exception as e:
        print(f"[PLC] Erro ao conectar: {e}", repr((e)))
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


def ler_bloco(offset_bytes: int, tamanho: int, chunk: int = 50):
    try:
        tamanho_bytes = tamanho * 4
        chunk_bytes = chunk * 4
        raw = bytearray()

        for pos in range(0, tamanho_bytes, chunk_bytes):
            leitura = min(chunk_bytes, tamanho_bytes - pos)
            raw.extend(plc.db_read(config.db, offset_bytes + pos, leitura))

        n = len(raw) // 4
        return list(struct.unpack_from(f">{n}f", raw))
    except Exception as e:
        print(f"PLC erro em db_read -> offset = ({offset_bytes}) : {e}")
        raise


def ler_vetores() -> dict[str, list[float]]:
    resultado = {}
    for nome, cfg in VETORES.items():
        print(f"[PLC] Lendo {nome} (offset={cfg['offset']}, {cfg['tamanho']} REALs)...")
        resultado[nome] = ler_bloco(cfg["offset"], cfg["tamanho"])
    return resultado
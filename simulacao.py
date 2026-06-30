import struct
import math
import random
from snap7.client import Client


# =========================
# CONFIGURAÇÃO CENTRAL
# =========================

MODO_SIMULACAO = True


class PLCConfig:
    def __init__(self):
        self.ip = "192.168.0.1"
        self.rack = 0
        self.slot = 2
        self.db = 3
        self.intervalo_s = 120

    def atualizar(self, ip: str, rack: int, slot: int, db: int):
        self.ip = ip
        self.rack = rack
        self.slot = slot
        self.db = db


config = PLCConfig()

# compatibilidade com UI antiga
INTERVALO_S = config.intervalo_s


# =========================
# MAPEAMENTO DE DADOS
# =========================

VETORES = {
    "Vetor 1": {"offset": 14,    "tamanho": 1599},
    "Vetor 2": {"offset": 6414,  "tamanho": 1599},
    "Vetor 3": {"offset": 12814, "tamanho": 1599},
}


# =========================
# CLIENTE SNAP7
# =========================

plc = Client()


# =========================
# CONEXÃO
# =========================

def conectar_plc() -> bool:
    if MODO_SIMULACAO:
        print("[SIMULAÇÃO] PLC conectado.")
        return True

    try:
        plc.connect(config.ip, config.rack, config.slot)
        return plc.get_connected()
    except Exception as e:
        print(f"[PLC] Erro ao conectar: {e}")
        return False


def desconectar_plc():
    if MODO_SIMULACAO:
        print("[SIMULAÇÃO] PLC desconectado.")
        return

    try:
        if plc.get_connected():
            plc.disconnect()
    except Exception as e:
        print(f"[PLC] Erro ao desconectar: {e}")


def esta_conectado() -> bool:
    if MODO_SIMULACAO:
        return True

    try:
        return plc.get_connected()
    except Exception:
        return False


# =========================
# LEITURA REAL (SNAP7)
# =========================

def ler_bloco(offset_bytes: int, tamanho: int, chunk: int = 50) -> list[float]:
    if MODO_SIMULACAO:
        return []

    tamanho_bytes = tamanho * 4
    chunk_bytes = chunk * 4
    raw = bytearray()

    for pos in range(0, tamanho_bytes, chunk_bytes):
        leitura = min(chunk_bytes, tamanho_bytes - pos)

        raw.extend(
            plc.db_read(
                config.db,
                offset_bytes + pos,
                leitura
            )
        )

    n = len(raw) // 4
    return list(struct.unpack_from(f">{n}f", raw))


# =========================
# SIMULAÇÃO REALISTA
# =========================

_contador = 0


def ler_vetores_fake() -> dict[str, list[float]]:
    global _contador

    n = 1599
    deslocamento = _contador * 5

    def ruido(v):
        return float(round(v, 4))

    vetor1 = [
        ruido(
            50
            + 10 * math.sin((i + deslocamento) / 20)
            + random.uniform(-0.5, 0.5)
        )
        for i in range(n)
    ]

    vetor2 = [
        ruido(
            30
            + 8 * math.cos((i + deslocamento) / 15)
            + random.uniform(-0.5, 0.5)
        )
        for i in range(n)
    ]

    vetor3 = [
        ruido(
            80
            + 20 * math.sin((i + deslocamento) / 30)
            + 5 * math.cos((i + deslocamento) / 10)
            + random.uniform(-1, 1)
        )
        for i in range(n)
    ]

    _contador += 1

    return {
        "Vetor 1": vetor1,
        "Vetor 2": vetor2,
        "Vetor 3": vetor3
    }


# =========================
# API PRINCIPAL
# =========================

def ler_vetores() -> dict[str, list[float]]:
    if MODO_SIMULACAO:
        print("[SIMULAÇÃO] Gerando vetores...")
        return ler_vetores_fake()

    resultado = {}

    for nome, cfg in VETORES.items():
        print(
            f"[PLC] Lendo {nome} "
            f"(offset={cfg['offset']}, {cfg['tamanho']} REALs)"
        )

        resultado[nome] = ler_bloco(
            cfg["offset"],
            cfg["tamanho"]
        )

    return resultado
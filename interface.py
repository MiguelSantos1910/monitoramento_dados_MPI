import time
import threading
import tkinter as tk
from tkinter import messagebox
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

import plc_client as plc
import mongo_client as mongo

#Constantes visuais
CORES       = ["#2196F3", "#4CAF50", "#F44336"]
INTERVALO_S = plc.INTERVALO_S

BG_DARK     = "#1e1e2e"
BG_DARKER   = "#13131f"
BTN_INATIVO = "#3a3a5c"


class AppPLC(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Monitor PLC – Leitura de Vetores")
        self.geometry("1100x780")
        self.configure(bg=BG_DARK)
        self.resizable(True, True)

        self._dados: dict[str, list[float]] = {}
        self._auto_ativo     = False
        self._timer_after    = None
        self._tempo_restante = 0

        self._build_ui()
        self._tentar_conexao()

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    #Layout
    def _build_ui(self):
        #Barra superior
        topo = tk.Frame(self, bg=BG_DARKER, pady=8)
        topo.pack(fill="x")

        tk.Label(
            topo, text="Monitor PLC",
            font=("Segoe UI", 14, "bold"),
            bg=BG_DARKER, fg="white"
        ).pack(side="left", padx=16)

        self.lbl_status = tk.Label(
            topo, text="⚪ Desconectado",
            font=("Segoe UI", 10),
            bg=BG_DARKER, fg="#aaaaaa"
        )
        self.lbl_status.pack(side="left", padx=12)

        tk.Button(
            topo, text="Reconectar",
            command=self._tentar_conexao,
            bg=BTN_INATIVO, fg="white",
            relief="flat", padx=10,
            font=("Segoe UI", 9)
        ).pack(side="left", padx=4)

        #Lado direito da barra
        self.btn_ler = tk.Button(
            topo, text="▶  Ler Agora",
            command=self._ler_manual,
            bg="#2196F3", fg="white",
            relief="flat", padx=14,
            font=("Segoe UI", 9, "bold")
        )
        self.btn_ler.pack(side="right", padx=8)

        self.btn_auto = tk.Button(
            topo, text="⏱  Auto: OFF",
            command=self._toggle_auto,
            bg=BTN_INATIVO, fg="#aaaaaa",
            relief="flat", padx=12,
            font=("Segoe UI", 9)
        )
        self.btn_auto.pack(side="right", padx=4)

        self.btn_exportar = tk.Button(
            topo, text="☁  Exportar",
            command=self._exportar_mongo,
            bg=BTN_INATIVO, fg="#aaaaaa",
            relief="flat", padx=12,
            font=("Segoe UI", 9)
        )
        self.btn_exportar.pack(side="right", padx=4)

        self.lbl_countdown = tk.Label(
            topo, text="",
            font=("Segoe UI", 9),
            bg=BG_DARKER, fg="#aaaaaa"
        )
        self.lbl_countdown.pack(side="right", padx=8)

        #Área dos gráficos
        frame_graf = tk.Frame(self, bg=BG_DARK)
        frame_graf.pack(fill="both", expand=True, padx=12, pady=(6, 4))

        plt.style.use("dark_background")
        self.fig = plt.Figure(figsize=(11, 7), facecolor=BG_DARK)
        gs = gridspec.GridSpec(3, 1, figure=self.fig, hspace=0.55)

        self.axes = []
        for i, (nome, cor) in enumerate(zip(plc.VETORES.keys(), CORES)):
            ax = self.fig.add_subplot(gs[i])
            self._estilizar_eixo(ax, nome, cor)
            self.axes.append((ax, cor, nome))

        self.canvas = FigureCanvasTkAgg(self.fig, master=frame_graf)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        toolbar_frame = tk.Frame(frame_graf, bg=BG_DARK)
        toolbar_frame.pack(fill="x")
        NavigationToolbar2Tk(self.canvas, toolbar_frame)

        #Rodapé
        self.lbl_rodape = tk.Label(
            self, text="Aguardando leitura...",
            font=("Segoe UI", 8),
            bg=BG_DARKER, fg="#666666",
            anchor="w", padx=12
        )
        self.lbl_rodape.pack(fill="x", side="bottom")

    def _estilizar_eixo(self, ax, nome: str, cor: str):
        ax.set_facecolor(BG_DARKER)
        ax.set_title(nome, color=cor, fontsize=10, pad=6)
        ax.set_xlabel("Índice", color="#888888", fontsize=8)
        ax.set_ylabel("Valor", color="#888888", fontsize=8)
        ax.tick_params(colors="#666666", labelsize=7)
        for spine in ax.spines.values():
            spine.set_edgecolor("#333355")

    #Conexão
    def _tentar_conexao(self):
        self.lbl_status.config(text="🟡 Conectando...", fg="#FFC107")
        self.update_idletasks()
        if plc.conectar_plc():
            self.lbl_status.config(text="🟢 Conectado", fg="#4CAF50")
            self._log("PLC conectado com sucesso.")
        else:
            self.lbl_status.config(text="🔴 Falha na conexão", fg="#F44336")
            self._log("Não foi possível conectar. Verifique IP/Rack/Slot em plc_client.py.")

    def _ler_manual(self):
        if not plc.esta_conectado():
            messagebox.showwarning("Desconectado", "PLC não está conectado.")
            return
        self.btn_ler.config(state="disabled", text="Lendo...")
        self._log("Leitura iniciada...")
        threading.Thread(target=self._tarefa_leitura, daemon=True).start()

    def _tarefa_leitura(self):
        try:
            dados = plc.ler_vetores()
            self._dados = dados
            self.after(0, self._atualizar_graficos)
        except Exception as e:
            self.after(0, lambda: self._log(f"Erro na leitura: {e}"))
        finally:
            self.after(0, lambda: self.btn_ler.config(
                state="normal", text="▶  Ler Agora"))

    # ── Atualiza gráficos
    def _atualizar_graficos(self):
        for (ax, cor, nome), valores in zip(self.axes, self._dados.values()):
            ax.cla()
            self._estilizar_eixo(ax, nome, cor)
            ax.plot(valores, color=cor, linewidth=0.8)
            ax.set_xlim(0, len(valores) - 1)

        self.canvas.draw()
        self._log(f"Gráficos atualizados às {time.strftime('%H:%M:%S')}.")

    def _exportar_mongo(self):
        if not self._dados:
            messagebox.showwarning("Sem dados", "Faça uma leitura antes de exportar.")
            return
        self.btn_exportar.config(state="disabled", text="Exportando...")
        self._log("Exportando para MongoDB...")

        def _tarefa():
            try:
                mongo.exportar(self._dados)
                self.after(0, lambda: self._log(
                    f"Exportado com sucesso às {time.strftime('%H:%M:%S')}."))
            except Exception as e:
                self.after(0, lambda: self._log(f"Erro no MongoDB: {e}"))
            finally:
                self.after(0, lambda: self.btn_exportar.config(
                    state="normal", text="☁  Exportar"))

        threading.Thread(target=_tarefa, daemon=True).start()

    #Auto atualização
    def _toggle_auto(self):
        if self._auto_ativo:
            self._parar_auto()
        else:
            if not plc.esta_conectado():
                messagebox.showwarning("Desconectado", "PLC não está conectado.")
                return
            self._iniciar_auto()

    def _iniciar_auto(self):
        self._auto_ativo = True
        self.btn_auto.config(text="⏱  Auto: ON", bg="#4CAF50", fg="white")
        self._log(f"Atualização automática ativada (a cada {INTERVALO_S}s).")
        self._ciclo_auto()

    def _parar_auto(self):
        self._auto_ativo = False
        if self._timer_after:
            self.after_cancel(self._timer_after)
            self._timer_after = None
        self.btn_auto.config(text="⏱  Auto: OFF", bg=BTN_INATIVO, fg="#aaaaaa")
        self.lbl_countdown.config(text="")
        self._log("Atualização automática desativada.")

    def _ciclo_auto(self):
        if not self._auto_ativo:
            return
        if not plc.esta_conectado():
            self._log("⚠️ Conexão perdida. Tentando reconectar...")
            if not plc.conectar_plc():
                self._parar_auto()
                self.lbl_status.config(text="🔴 Falha na conexão", fg="#F44336")
                return
            self.lbl_status.config(text="🟢 Conectado", fg="#4CAF50")

        threading.Thread(target=self._tarefa_leitura, daemon=True).start()
        self._tempo_restante = INTERVALO_S
        self._tick_countdown()

    def _tick_countdown(self):
        if not self._auto_ativo:
            self.lbl_countdown.config(text="")
            return
        if self._tempo_restante > 0:
            self.lbl_countdown.config(text=f"próxima em {self._tempo_restante}s")
            self._tempo_restante -= 1
            self._timer_after = self.after(1000, self._tick_countdown)
        else:
            self._ciclo_auto()

    #Log rodapé
    def _log(self, msg: str):
        self.lbl_rodape.config(text=f"● {msg}")

    #Fechar app
    def on_close(self):
        self._auto_ativo = False
        if self._timer_after:
            self.after_cancel(self._timer_after)
        plc.desconectar_plc()
        self.destroy()


if __name__ == "__main__":
    app = AppPLC()
    app.mainloop()
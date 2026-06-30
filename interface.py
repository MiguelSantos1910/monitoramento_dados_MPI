import time
import threading
import tkinter as tk
from tkinter import messagebox
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

import simulacao as plc
import mongo_client as mongo
import sys, os

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

#Constantes visuais
CORES       = ["#2196F3", "#4CAF50", "#F44336"]
INTERVALO_S = plc.config.intervalo_s

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

        self.iconbitmap(resource_path("senai.ico"))

        self._build_ui()
        self._tentar_conexao()

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    #Layout
    def _build_ui(self):
        #Barra superior
        topo = tk.Frame(self, bg=BG_DARKER, pady=8)
        topo.pack(fill="x")

        self._linhas = {}
        self._tooltips = {}

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
            command=self._abrir_dialogo_exportacao,
            bg=BTN_INATIVO, fg="#aaaaaa",
            relief="flat", padx=12,
            font=("Segoe UI", 9)
        )
        self.btn_exportar.pack(side="right", padx=4)

        self.btn_config = tk.Button(
            topo,
            text="⚙ Config PLC",
            command=self._abrir_config_plc,
            bg="#3a3a5c",
            fg="white",
            relief="flat",
            padx=12,
            font=("Segoe UI", 9)
        )

        self.btn_config.pack(side="right", padx=4)

        self.btn_comparar = tk.Button(
            topo,
            text="📊 Comparar Gráficos",
            command=self._comparar_graficos,
            bg=BTN_INATIVO,
            fg="white",
            relief="flat",
            padx=12,
            font=("Segoe UI", 9)
        )
        self.btn_comparar.pack(side="right", padx=4)

        self.lbl_countdown = tk.Label(
            topo, text="",
            font=("Segoe UI", 9),
            bg=BG_DARKER, fg="#aaaaaa"
        )
        self.lbl_countdown.pack(side="right", padx=8)

        self.lbl_plc_ip = tk.Label(
            topo, text=f"IP: {plc.config.ip}",
            font=("Segoe UI", 9),
            bg=BG_DARKER, fg="#aaaaaa"
        )
        self.lbl_plc_ip.pack(side="right", padx=2)

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

            tooltip = ax.annotate(
                "",
                xy=(0, 0),
                xytext=(10, 10),
                textcoords="offset points",
                color="white",
                bbox=dict(
                    boxstyle="round",
                    fc="black",
                    alpha=0.8
                )
            )

            tooltip.set_visible(False)

            self._tooltips[ax] = tooltip
            self.axes.append((ax, cor, nome))
            

        self.canvas = FigureCanvasTkAgg(self.fig, master=frame_graf)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        self.canvas.mpl_connect("motion_notify_event", self._on_graph_move)

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
            self.after(0, lambda: self._log(f"Erro na leitura: {e}", ))
        finally:
            self.after(0, lambda: self.btn_ler.config(
                state="normal", text="▶  Ler Agora"))

    # ── Atualiza gráficos
    def _atualizar_graficos(self):
        self._linhas.clear()

        for (ax, cor, nome), valores in zip(
            self.axes,
            self._dados.values()
        ):

            ax.cla()

            self._estilizar_eixo(
                ax,
                nome,
                cor
            )

            tooltip = ax.annotate(
                "",
                xy=(0, 0),
                xytext=(10, 10),
                textcoords="offset points",
                color="white",
                bbox=dict(
                    boxstyle="round",
                    fc="black",
                    alpha=0.85
                )
            )

            tooltip.set_visible(False)

            self._tooltips[ax] = tooltip

            line, = ax.plot(
                valores,
                color=cor,
                linewidth=1.0
            )

            self._linhas[ax] = (
                line,
                valores
            )

            ax.set_xlim(
                0,
                len(valores) - 1
            )

        self.canvas.draw()

        self._log(
            f"Gráficos atualizados às {time.strftime('%H:%M:%S')}"
        )

    def _exportar_mongo_com_dados(self, garra, pressao, operacao):
        if not self._dados:
            messagebox.showwarning("Sem dados", "Faça uma leitura antes de exportar.")
            return

        self.btn_exportar.config(state="disabled", text="Exportando...")
        self._log("Exportando para MongoDB...")

        valores = {
            k: list(v) for k, v in self._dados.items()
        }

        documento = {
            "garra": garra,
            "pressao": float(pressao),
            "operacao": operacao,
            "valores": valores,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "modo": "simulacao" if plc.MODO_SIMULACAO else "real"
        }

        def tarefa():
            try:
                mongo.exportar(documento)
                self.after(0, lambda: self._log("Exportado com sucesso!"))
            except Exception as e:
                err = str(e) 
                self.after(0, lambda err=err: self._log(f"Erro MongoDB: {err}"))
            finally:
                self.after(0, lambda: self.btn_exportar.config(
                    state="normal",
                    text="☁ Exportar"
                ))

        threading.Thread(target=tarefa, daemon=True).start()

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
    
    #Junta os vetores em um único gráfico
    def _comparar_graficos(self):
        if not self._dados:
            messagebox.showwarning(
                "Sem dados",
                "Faça uma leitura antes."
            )
            return

        janela = tk.Toplevel(self)
        janela.title("Comparação dos Vetores")
        janela.geometry("1000x600")
        janela.configure(bg=BG_DARK)

        fig = plt.Figure(
            figsize=(10, 5),
            facecolor=BG_DARK
        )

        ax = fig.add_subplot(111)
        ax.set_facecolor(BG_DARKER)

        for nome, cor in zip(self._dados.keys(), CORES):
            ax.plot(
                self._dados[nome],
                label=nome,
                color=cor,
                linewidth=1.2
            )

        ax.set_title(
            "Comparação dos Vetores",
            color="white"
        )

        ax.set_xlabel(
            "Amostra",
            color="#888888"
        )

        ax.set_ylabel(
            "Valor",
            color="#888888"
        )

        ax.tick_params(colors="#888888")
        ax.grid(True, alpha=0.2)
        ax.legend()

        canvas = FigureCanvasTkAgg(
            fig,
            master=janela
        )

        canvas.draw()
        canvas.get_tk_widget().pack(
            fill="both",
            expand=True
        )

        toolbar_frame = tk.Frame(
            janela,
            bg=BG_DARK
        )

        toolbar_frame.pack(fill="x")

        NavigationToolbar2Tk(
            canvas,
            toolbar_frame
        )

    def _on_graph_move(self, event):

        if event.inaxes is None:

            for tooltip in self._tooltips.values():
                tooltip.set_visible(False)

            self.canvas.draw_idle()
            return

        ax = event.inaxes

        if ax not in self._linhas:
            return

        line, valores = self._linhas[ax]
        tooltip = self._tooltips[ax]

        for t in self._tooltips.values():
            t.set_visible(False)

        if event.xdata is None:
            return

        idx = int(round(event.xdata))

        if 0 <= idx < len(valores):

            y = valores[idx]

            tooltip.xy = (idx, y)

            tooltip.set_text(
                f"Amostra: {idx}\n"
                f"Valor: {y:.2f}"
            )

            tooltip.set_visible(True)

            self.lbl_rodape.config(
                text=f"{ax.get_title()} | Amostra {idx} | Valor {y:.2f}"
            )

        self.canvas.draw_idle()
    
    def _abrir_dialogo_exportacao(self):
        janela = tk.Toplevel(self)
        janela.title("Exportar para MongoDB")
        janela.geometry("320x260")
        janela.configure(bg=BG_DARK)
        janela.grab_set()

        tk.Label(janela, text="Nome da Garra:", bg=BG_DARK, fg="white").pack(pady=(10, 0))
        entry_garra = tk.Entry(janela)
        entry_garra.pack()

        tk.Label(janela, text="Pressão:", bg=BG_DARK, fg="white").pack(pady=(10, 0))
        entry_pressao = tk.Entry(janela)
        entry_pressao.pack()

        tk.Label(janela, text="Operação:", bg=BG_DARK, fg="white").pack(pady=(10, 0))
        op_var = tk.StringVar(value="carga")
        tk.OptionMenu(janela, op_var, "carga", "descarga").pack()

        def confirmar():
            garra = entry_garra.get().strip()
            pressao = entry_pressao.get().strip()
            operacao = op_var.get()

            if not garra or not pressao:
                messagebox.showwarning("Erro", "Preencha todos os campos!")
                return

            self._exportar_mongo_com_dados(garra, pressao, operacao)
            janela.destroy()

        tk.Button(
            janela,
            text="Exportar",
            command=confirmar,
            bg="#4CAF50",
            fg="white"
        ).pack(pady=15)

    def _abrir_config_plc(self):
        janela = tk.Toplevel(self)
        janela.title("Configuração PLC")
        janela.geometry("300x250")
        janela.configure(bg=BG_DARK)
        janela.grab_set()

        tk.Label(janela, text="IP:", bg=BG_DARK, fg="white").pack()
        entry_ip = tk.Entry(janela)
        entry_ip.insert(0, plc.config.ip)
        entry_ip.pack()

        tk.Label(janela, text="Rack:", bg=BG_DARK, fg="white").pack()
        entry_rack = tk.Entry(janela)
        entry_rack.insert(0, str(plc.config.rack))
        entry_rack.pack()

        tk.Label(janela, text="Slot:", bg=BG_DARK, fg="white").pack()
        entry_slot = tk.Entry(janela)
        entry_slot.insert(0, str(plc.config.slot))
        entry_slot.pack()

        tk.Label(janela, text="DB:", bg=BG_DARK, fg="white").pack()
        entry_db = tk.Entry(janela)
        entry_db.insert(0, str(plc.config.db))
        entry_db.pack()

        def salvar():
            plc.config.atualizar(
                entry_ip.get().strip(),
                int(entry_rack.get()),
                int(entry_slot.get()),
                int(entry_db.get())
            )

            self._log("Config PLC atualizada. Reconectando...")
            self._atualizar_ip_plc()
            plc.desconectar_plc()
            plc.conectar_plc()

            janela.destroy()

        tk.Button(
            janela,
            text="Salvar",
            command=salvar,
            bg="#4CAF50",
            fg="white"
        ).pack(pady=15)

    def _atualizar_ip_plc(self):
        self.lbl_plc_ip.config(
            text=f"IP: {plc.config.ip}"
        )

if __name__ == "__main__":
    app = AppPLC()
    app.mainloop()
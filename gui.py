"""
Interface Gráfica do Sistema de Pedidos
Monitora em tempo real o estado do sistema, processos e memória compartilhada
"""
import tkinter as tk
from tkinter import ttk, scrolledtext
import time
import psutil
import os
import signal
from threading import Thread
from shared_memory_manager import SharedMemoryManager, PedidoStatus

class SistemaGUI:
    """Interface gráfica para monitoramento do sistema"""

    def __init__(self, processos_dict):
        self.processos = processos_dict
        self.root = tk.Tk()
        self.root.title("Sistema de Gerenciamento de Pedidos - Restaurante")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f0f0')

        # Cores
        self.cor_bg = '#f0f0f0'
        self.cor_frame = '#ffffff'
        self.cor_header = '#2c3e50'
        self.cor_pendente = '#f39c12'
        self.cor_preparo = '#3498db'
        self.cor_concluido = '#27ae60'

        self.shm_manager = None
        self.rodando = True

        self.criar_interface()
        self.iniciar_atualizacao()

    def criar_interface(self):
        """Cria todos os componentes da interface"""

        # Título
        titulo_frame = tk.Frame(self.root, bg=self.cor_header, height=60)
        titulo_frame.pack(fill=tk.X, padx=0, pady=0)
        titulo_frame.pack_propagate(False)

        titulo = tk.Label(
            titulo_frame,
            text="🍽️ Sistema de Gerenciamento de Pedidos",
            font=("Arial", 20, "bold"),
            bg=self.cor_header,
            fg='white'
        )
        titulo.pack(pady=15)

        # Frame principal
        main_frame = tk.Frame(self.root, bg=self.cor_bg)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Painel esquerdo - Estatísticas e Processos
        left_frame = tk.Frame(main_frame, bg=self.cor_bg)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        self.criar_painel_estatisticas(left_frame)
        self.criar_painel_processos(left_frame)

        # Painel direito - Pedidos
        right_frame = tk.Frame(main_frame, bg=self.cor_bg)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        self.criar_painel_pedidos(right_frame)
        self.criar_painel_logs(right_frame)

    def criar_painel_estatisticas(self, parent):
        """Cria painel de estatísticas"""
        frame = tk.LabelFrame(
            parent,
            text="📊 Estatísticas do Sistema",
            font=("Arial", 12, "bold"),
            bg=self.cor_frame,
            padx=10,
            pady=10
        )
        frame.pack(fill=tk.X, pady=(0, 10))

        # Grid de estatísticas
        stats_grid = tk.Frame(frame, bg=self.cor_frame)
        stats_grid.pack(fill=tk.X)

        # Total Criados
        self.label_total_criados = self.criar_stat_label(
            stats_grid, "Total Criados", "0", self.cor_header, 0, 0
        )

        # Total Processados
        self.label_total_processados = self.criar_stat_label(
            stats_grid, "Processados", "0", self.cor_concluido, 0, 1
        )

        # Em Fila
        self.label_em_fila = self.criar_stat_label(
            stats_grid, "Em Fila", "0", self.cor_pendente, 1, 0
        )

        # Em Preparo
        self.label_em_preparo = self.criar_stat_label(
            stats_grid, "Em Preparo", "0", self.cor_preparo, 1, 1
        )

    def criar_stat_label(self, parent, texto, valor, cor, row, col):
        """Cria um label de estatística"""
        container = tk.Frame(parent, bg=cor, relief=tk.RAISED, borderwidth=2)
        container.grid(row=row, column=col, padx=5, pady=5, sticky='ew')
        parent.grid_columnconfigure(col, weight=1)

        label_texto = tk.Label(
            container,
            text=texto,
            font=("Arial", 10),
            bg=cor,
            fg='white'
        )
        label_texto.pack(pady=(5, 0))

        label_valor = tk.Label(
            container,
            text=valor,
            font=("Arial", 24, "bold"),
            bg=cor,
            fg='white'
        )
        label_valor.pack(pady=(0, 5))

        return label_valor

    def criar_painel_processos(self, parent):
        """Cria painel de monitoramento de processos"""
        frame = tk.LabelFrame(
            parent,
            text="⚙️ Processos Ativos",
            font=("Arial", 12, "bold"),
            bg=self.cor_frame,
            padx=10,
            pady=10
        )
        frame.pack(fill=tk.BOTH, expand=True)

        # Treeview para processos
        columns = ('Tipo', 'ID', 'PID', 'Status', 'CPU%', 'MEM (MB)')
        self.tree_processos = ttk.Treeview(frame, columns=columns, show='headings', height=8)

        for col in columns:
            self.tree_processos.heading(col, text=col)
            if col == 'Tipo':
                self.tree_processos.column(col, width=100)
            elif col in ['ID', 'PID', 'Status']:
                self.tree_processos.column(col, width=80)
            else:
                self.tree_processos.column(col, width=70)

        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.tree_processos.yview)
        self.tree_processos.configure(yscroll=scrollbar.set)

        self.tree_processos.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def criar_painel_pedidos(self, parent):
        """Cria painel de pedidos"""
        frame = tk.LabelFrame(
            parent,
            text="📋 Fila de Pedidos",
            font=("Arial", 12, "bold"),
            bg=self.cor_frame,
            padx=10,
            pady=10
        )
        frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Treeview para pedidos
        columns = ('ID', 'Mesa', 'Item', 'Status', 'Produtor', 'Consumidor')
        self.tree_pedidos = ttk.Treeview(frame, columns=columns, show='headings', height=15)

        for col in columns:
            self.tree_pedidos.heading(col, text=col)
            if col == 'Item':
                self.tree_pedidos.column(col, width=150)
            elif col == 'ID':
                self.tree_pedidos.column(col, width=80)
            else:
                self.tree_pedidos.column(col, width=80)

        # Tags para cores
        self.tree_pedidos.tag_configure('pendente', background='#fff3cd')
        self.tree_pedidos.tag_configure('preparo', background='#cfe2ff')
        self.tree_pedidos.tag_configure('concluido', background='#d1e7dd')

        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.tree_pedidos.yview)
        self.tree_pedidos.configure(yscroll=scrollbar.set)

        self.tree_pedidos.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def criar_painel_logs(self, parent):
        """Cria painel de logs"""
        frame = tk.LabelFrame(
            parent,
            text="📝 Logs do Sistema",
            font=("Arial", 12, "bold"),
            bg=self.cor_frame,
            padx=10,
            pady=10
        )
        frame.pack(fill=tk.BOTH, expand=True)

        self.text_logs = scrolledtext.ScrolledText(
            frame,
            height=10,
            font=("Courier", 9),
            bg='#1e1e1e',
            fg='#d4d4d4',
            insertbackground='white'
        )
        self.text_logs.pack(fill=tk.BOTH, expand=True)

    def atualizar_interface(self):
        """Atualiza a interface com dados da memória compartilhada"""
        try:
            if not self.shm_manager:
                self.shm_manager = SharedMemoryManager(create=False)

            # Atualizar estatísticas
            stats = self.shm_manager.obter_estatisticas()
            self.label_total_criados.config(text=str(stats.get('total_criados', 0)))
            self.label_total_processados.config(text=str(stats.get('total_processados', 0)))

            # Obter todos os pedidos
            pedidos = self.shm_manager.obter_todos_pedidos()

            # Contar pedidos por status
            em_fila = sum(1 for p in pedidos if p.status == PedidoStatus.PENDENTE.value)
            em_preparo = sum(1 for p in pedidos if p.status == PedidoStatus.EM_PREPARO.value)

            self.label_em_fila.config(text=str(em_fila))
            self.label_em_preparo.config(text=str(em_preparo))

            # Atualizar tabela de pedidos
            self.tree_pedidos.delete(*self.tree_pedidos.get_children())

            for pedido in reversed(pedidos[-30:]):  # Mostrar últimos 30
                consumidor_str = str(pedido.consumidor_id) if pedido.consumidor_id != -1 else '-'

                tag = ''
                if pedido.status == PedidoStatus.PENDENTE.value:
                    tag = 'pendente'
                elif pedido.status == PedidoStatus.EM_PREPARO.value:
                    tag = 'preparo'
                else:
                    tag = 'concluido'

                self.tree_pedidos.insert('', 'end', values=(
                    pedido.id,
                    pedido.mesa,
                    pedido.item,
                    pedido.status,
                    pedido.produtor_id,
                    consumidor_str
                ), tags=(tag,))

            # Atualizar processos
            self.atualizar_processos()

        except Exception as e:
            self.adicionar_log(f"Erro ao atualizar interface: {e}")

    def atualizar_processos(self):
        """Atualiza informações dos processos"""
        self.tree_processos.delete(*self.tree_processos.get_children())

        for tipo, lista_processos in self.processos.items():
            for proc_info in lista_processos:
                proc = proc_info['process']
                proc_id = proc_info['id']

                try:
                    if proc.is_alive():
                        processo = psutil.Process(proc.pid)
                        cpu = processo.cpu_percent(interval=0.1)
                        mem = processo.memory_info().rss / 1024 / 1024  # MB
                        status = "Ativo"
                    else:
                        cpu = 0
                        mem = 0
                        status = "Inativo"

                    self.tree_processos.insert('', 'end', values=(
                        tipo.capitalize(),
                        proc_id,
                        proc.pid if proc.is_alive() else '-',
                        status,
                        f"{cpu:.1f}",
                        f"{mem:.1f}"
                    ))
                except:
                    self.tree_processos.insert('', 'end', values=(
                        tipo.capitalize(),
                        proc_id,
                        '-',
                        "Erro",
                        '-',
                        '-'
                    ))

    def adicionar_log(self, mensagem):
        """Adiciona mensagem ao log"""
        timestamp = time.strftime("%H:%M:%S")
        self.text_logs.insert(tk.END, f"[{timestamp}] {mensagem}\n")
        self.text_logs.see(tk.END)

    def iniciar_atualizacao(self):
        """Inicia thread de atualização"""
        def loop_atualizacao():
            while self.rodando:
                try:
                    self.root.after(0, self.atualizar_interface)
                    time.sleep(1)
                except:
                    break

        thread = Thread(target=loop_atualizacao, daemon=True)
        thread.start()

        self.adicionar_log("Sistema iniciado")

    def executar(self):
        """Inicia a interface gráfica"""
        try:
            self.root.mainloop()
        finally:
            self.rodando = False
            if self.shm_manager:
                self.shm_manager.close()

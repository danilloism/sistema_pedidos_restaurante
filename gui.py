"""
Interface Gráfica com Controle de Execução
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import time
import psutil
from threading import Thread, Timer
from shared_memory_manager import SharedMemoryManager, PedidoStatus
from datetime import datetime
import csv
import json

class SistemaGUI:
    def __init__(self, sistema):
        self.sistema = sistema
        self.root = tk.Tk()
        self.root.title("Sistema de Gerenciamento de Pedidos - Restaurante")
        self.root.geometry("1300x850")
        self.root.configure(bg='#f0f0f0')

        self.cor_bg = '#f0f0f0'
        self.cor_frame = '#ffffff'
        self.cor_header = '#2c3e50'
        self.cor_sucesso = '#27ae60'
        self.cor_pendente = '#f39c12'
        self.cor_preparo = '#3498db'
        self.cor_concluido = '#27ae60'

        self.shm_manager = None
        self.rodando = False
        self.sistema_iniciado = False
        self.timer_parada = None

        self.criar_interface()

    def criar_interface(self):
        # Título
        titulo_frame = tk.Frame(self.root, bg=self.cor_header, height=60)
        titulo_frame.pack(fill=tk.X)
        titulo_frame.pack_propagate(False)

        titulo = tk.Label(titulo_frame, text="🍽️ Sistema de Gerenciamento de Pedidos",
                         font=("Arial", 20, "bold"), bg=self.cor_header, fg='white')
        titulo.pack(pady=15)

        # Painel de controle no topo
        self.criar_painel_controle()

        # Frame principal
        main_frame = tk.Frame(self.root, bg=self.cor_bg)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        left_frame = tk.Frame(main_frame, bg=self.cor_bg)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        self.criar_painel_estatisticas(left_frame)
        self.criar_painel_processos(left_frame)

        right_frame = tk.Frame(main_frame, bg=self.cor_bg)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        self.criar_painel_pedidos(right_frame)
        self.criar_painel_logs(right_frame)

    def criar_painel_controle(self):
        """Painel de controle com configurações e botões"""
        frame = tk.LabelFrame(self.root, text="⚙️ Controle do Sistema",
                             font=("Arial", 12, "bold"), bg=self.cor_frame, padx=15, pady=15)
        frame.pack(fill=tk.X, padx=10, pady=(10, 0))

        # Container para organizar em grid
        grid_frame = tk.Frame(frame, bg=self.cor_frame)
        grid_frame.pack(fill=tk.X)

        # Linha 1: Configurações
        tk.Label(grid_frame, text="Nº Produtores:", font=("Arial", 10),
                bg=self.cor_frame).grid(row=0, column=0, padx=5, pady=5, sticky='e')

        self.spin_produtores = ttk.Spinbox(grid_frame, from_=1, to=10, width=10)
        self.spin_produtores.set(2)
        self.spin_produtores.grid(row=0, column=1, padx=5, pady=5, sticky='w')

        tk.Label(grid_frame, text="Nº Consumidores:", font=("Arial", 10),
                bg=self.cor_frame).grid(row=0, column=2, padx=5, pady=5, sticky='e')

        self.spin_consumidores = ttk.Spinbox(grid_frame, from_=1, to=10, width=10)
        self.spin_consumidores.set(3)
        self.spin_consumidores.grid(row=0, column=3, padx=5, pady=5, sticky='w')

        tk.Label(grid_frame, text="Duração (segundos):", font=("Arial", 10),
                bg=self.cor_frame).grid(row=0, column=4, padx=5, pady=5, sticky='e')

        self.spin_duracao = ttk.Spinbox(grid_frame, from_=0, to=600, width=10)
        self.spin_duracao.set(0)
        self.spin_duracao.grid(row=0, column=5, padx=5, pady=5, sticky='w')

        tk.Label(grid_frame, text="(0 = ilimitado)", font=("Arial", 8, "italic"),
                bg=self.cor_frame, fg='gray').grid(row=0, column=6, padx=5, pady=5, sticky='w')

        # Linha 2: Botões de ação
        btn_frame = tk.Frame(frame, bg=self.cor_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))

        self.btn_iniciar = tk.Button(btn_frame, text="▶️ INICIAR SISTEMA",
                                     font=("Arial", 12, "bold"), bg=self.cor_sucesso,
                                     fg='white', command=self.iniciar_sistema,
                                     padx=20, pady=10, cursor='hand2')
        self.btn_iniciar.pack(side=tk.LEFT, padx=5)

        self.btn_parar = tk.Button(btn_frame, text="⏹️ PARAR SISTEMA",
                                   font=("Arial", 12, "bold"), bg='#e74c3c',
                                   fg='white', command=self.parar_sistema,
                                   padx=20, pady=10, cursor='hand2', state=tk.DISABLED)
        self.btn_parar.pack(side=tk.LEFT, padx=5)

        self.btn_limpar = tk.Button(btn_frame, text="🧹 LIMPAR DADOS",
                                    font=("Arial", 12), bg='#95a5a6',
                                    fg='white', command=self.limpar_dados,
                                    padx=20, pady=10, cursor='hand2')
        self.btn_limpar.pack(side=tk.LEFT, padx=5)

        self.btn_exportar = tk.Button(btn_frame, text="📊 EXPORTAR DADOS",
                                      font=("Arial", 12), bg='#3498db',
                                      fg='white', command=self.exportar_dados,
                                      padx=20, pady=10, cursor='hand2')
        self.btn_exportar.pack(side=tk.LEFT, padx=5)

        # Label de status
        self.label_status = tk.Label(btn_frame, text="● Sistema Parado",
                                     font=("Arial", 12, "bold"), bg=self.cor_frame,
                                     fg='#e74c3c')
        self.label_status.pack(side=tk.RIGHT, padx=10)

    def criar_painel_estatisticas(self, parent):
        frame = tk.LabelFrame(parent, text="📊 Estatísticas do Sistema",
                             font=("Arial", 12, "bold"), bg=self.cor_frame, padx=10, pady=10)
        frame.pack(fill=tk.X, pady=(0, 10))

        stats_grid = tk.Frame(frame, bg=self.cor_frame)
        stats_grid.pack(fill=tk.X)

        self.label_total_criados = self.criar_stat_label(stats_grid, "Total Criados", "0", self.cor_header, 0, 0)
        self.label_total_processados = self.criar_stat_label(stats_grid, "Processados", "0", self.cor_concluido, 0, 1)
        self.label_em_fila = self.criar_stat_label(stats_grid, "Em Fila", "0", self.cor_pendente, 1, 0)
        self.label_em_preparo = self.criar_stat_label(stats_grid, "Em Preparo", "0", self.cor_preparo, 1, 1)

    def criar_stat_label(self, parent, texto, valor, cor, row, col):
        container = tk.Frame(parent, bg=cor, relief=tk.RAISED, borderwidth=2)
        container.grid(row=row, column=col, padx=5, pady=5, sticky='ew')
        parent.grid_columnconfigure(col, weight=1)

        tk.Label(container, text=texto, font=("Arial", 10), bg=cor, fg='white').pack(pady=(5, 0))
        label_valor = tk.Label(container, text=valor, font=("Arial", 24, "bold"), bg=cor, fg='white')
        label_valor.pack(pady=(0, 5))
        return label_valor

    def criar_painel_processos(self, parent):
        frame = tk.LabelFrame(parent, text="⚙️ Processos Ativos",
                             font=("Arial", 12, "bold"), bg=self.cor_frame, padx=10, pady=10)
        frame.pack(fill=tk.BOTH, expand=True)

        columns = ('Tipo', 'ID', 'PID', 'Status', 'CPU%', 'MEM (MB)')
        self.tree_processos = ttk.Treeview(frame, columns=columns, show='headings', height=8)

        for col in columns:
            self.tree_processos.heading(col, text=col)
            self.tree_processos.column(col, width=100 if col == 'Tipo' else 80)

        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.tree_processos.yview)
        self.tree_processos.configure(yscroll=scrollbar.set)
        self.tree_processos.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def criar_painel_pedidos(self, parent):
        frame = tk.LabelFrame(parent, text="📋 Fila de Pedidos",
                             font=("Arial", 12, "bold"), bg=self.cor_frame, padx=10, pady=10)
        frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        columns = ('ID', 'Mesa', 'Item', 'Status', 'Produtor', 'Consumidor')
        self.tree_pedidos = ttk.Treeview(frame, columns=columns, show='headings', height=15)

        for col in columns:
            self.tree_pedidos.heading(col, text=col)
            self.tree_pedidos.column(col, width=150 if col == 'Item' else 80)

        self.tree_pedidos.tag_configure('pendente', background='#fff3cd')
        self.tree_pedidos.tag_configure('preparo', background='#cfe2ff')
        self.tree_pedidos.tag_configure('concluido', background='#d1e7dd')

        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.tree_pedidos.yview)
        self.tree_pedidos.configure(yscroll=scrollbar.set)
        self.tree_pedidos.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def criar_painel_logs(self, parent):
        frame = tk.LabelFrame(parent, text="📝 Logs do Sistema",
                             font=("Arial", 12, "bold"), bg=self.cor_frame, padx=10, pady=10)
        frame.pack(fill=tk.BOTH, expand=True)

        self.text_logs = scrolledtext.ScrolledText(frame, height=10, font=("Courier", 9),
                                                   bg='#1e1e1e', fg='#d4d4d4')
        self.text_logs.pack(fill=tk.BOTH, expand=True)

    def iniciar_sistema(self):
        """Inicia o sistema com os parâmetros configurados"""
        if self.sistema_iniciado:
            messagebox.showwarning("Aviso", "O sistema já está em execução!")
            return

        try:
            num_produtores = int(self.spin_produtores.get())
            num_consumidores = int(self.spin_consumidores.get())
            duracao = int(self.spin_duracao.get())

            # Validações
            if num_produtores < 1 or num_produtores > 10:
                messagebox.showerror("Erro", "Número de produtores deve estar entre 1 e 10")
                return

            if num_consumidores < 1 or num_consumidores > 10:
                messagebox.showerror("Erro", "Número de consumidores deve estar entre 1 e 10")
                return

            # Desabilitar controles
            self.spin_produtores.config(state='disabled')
            self.spin_consumidores.config(state='disabled')
            self.spin_duracao.config(state='disabled')
            self.btn_iniciar.config(state=tk.DISABLED)
            self.btn_parar.config(state=tk.NORMAL)

            # Atualizar status
            self.label_status.config(text="● Sistema Executando", fg=self.cor_sucesso)

            # Adicionar log
            self.adicionar_log(f"Iniciando sistema: {num_produtores} produtores, {num_consumidores} consumidores")

            if duracao > 0:
                self.adicionar_log(f"Duração configurada: {duracao} segundos")
            else:
                self.adicionar_log("Duração: Ilimitada")

            # Criar processos
            self.sistema.criar_processos(num_produtores, num_consumidores)

            self.sistema_iniciado = True
            self.rodando = True

            # Iniciar atualização da interface
            self.iniciar_atualizacao()

            # Configurar timer de parada se necessário
            if duracao > 0:
                self.timer_parada = Timer(duracao, self.parar_sistema_automatico)
                self.timer_parada.start()
                self.adicionar_log(f"Timer de {duracao}s iniciado")

        except ValueError as e:
            messagebox.showerror("Erro", f"Valores inválidos: {e}")

    def parar_sistema(self):
        """Para o sistema manualmente"""
        if not self.sistema_iniciado:
            return

        if messagebox.askyesno("Confirmar", "Deseja realmente parar o sistema?"):
            self.parar_sistema_interno()

    def parar_sistema_automatico(self):
        """Para o sistema automaticamente após tempo configurado"""
        self.adicionar_log("⏰ Tempo limite atingido - Parando sistema...")
        self.root.after(0, self.parar_sistema_interno)

    def parar_sistema_interno(self):
        """Lógica interna de parada"""
        self.adicionar_log("Parando sistema...")

        # Cancelar timer se existir
        if self.timer_parada:
            self.timer_parada.cancel()

        # Parar atualização
        self.rodando = False

        # Encerrar processos
        self.sistema.encerrar_processos()

        # Reabilitar controles
        self.spin_produtores.config(state='normal')
        self.spin_consumidores.config(state='normal')
        self.spin_duracao.config(state='normal')
        self.btn_iniciar.config(state=tk.NORMAL)
        self.btn_parar.config(state=tk.DISABLED)

        # Atualizar status
        self.label_status.config(text="● Sistema Parado", fg='#e74c3c')

        self.sistema_iniciado = False
        self.adicionar_log("✓ Sistema parado com sucesso")

    def limpar_dados(self):
        """Limpa os dados da memória compartilhada"""
        if self.sistema_iniciado:
            messagebox.showwarning("Aviso", "Pare o sistema antes de limpar os dados!")
            return

        if messagebox.askyesno("Confirmar", "Deseja limpar todos os dados?"):
            self.sistema.limpar_memoria()
            self.adicionar_log("🧹 Dados limpos")

            # Limpar interface
            self.tree_pedidos.delete(*self.tree_pedidos.get_children())
            self.label_total_criados.config(text="0")
            self.label_total_processados.config(text="0")
            self.label_em_fila.config(text="0")
            self.label_em_preparo.config(text="0")

    def atualizar_interface(self):
        """Atualiza a interface com dados da memória"""
        try:
            if not self.shm_manager:
                self.shm_manager = SharedMemoryManager(create=False)

            stats = self.shm_manager.obter_estatisticas()
            self.label_total_criados.config(text=str(stats.get('total_criados', 0)))
            self.label_total_processados.config(text=str(stats.get('total_processados', 0)))

            pedidos = self.shm_manager.obter_todos_pedidos()
            em_fila = sum(1 for p in pedidos if p.status == PedidoStatus.PENDENTE.value)
            em_preparo = sum(1 for p in pedidos if p.status == PedidoStatus.EM_PREPARO.value)

            self.label_em_fila.config(text=str(em_fila))
            self.label_em_preparo.config(text=str(em_preparo))

            self.tree_pedidos.delete(*self.tree_pedidos.get_children())
            for pedido in reversed(pedidos[-30:]):
                consumidor_str = str(pedido.consumidor_id) if pedido.consumidor_id != -1 else '-'
                tag = 'pendente' if pedido.status == PedidoStatus.PENDENTE.value else \
                      'preparo' if pedido.status == PedidoStatus.EM_PREPARO.value else 'concluido'
                self.tree_pedidos.insert('', 'end', values=(
                    pedido.id, pedido.mesa, pedido.item, pedido.status, pedido.produtor_id, consumidor_str
                ), tags=(tag,))

            self.atualizar_processos()
        except Exception as e:
            pass

    def atualizar_processos(self):
        """Atualiza informações dos processos"""
        self.tree_processos.delete(*self.tree_processos.get_children())
        for tipo, lista_processos in self.sistema.processos.items():
            for proc_info in lista_processos:
                proc = proc_info['process']
                try:
                    if proc.is_alive():
                        processo = psutil.Process(proc.pid)
                        cpu = processo.cpu_percent(interval=0.1)
                        mem = processo.memory_info().rss / 1024 / 1024
                        status = "Ativo"
                    else:
                        cpu, mem, status = 0, 0, "Inativo"

                    self.tree_processos.insert('', 'end', values=(
                        tipo.capitalize(), proc_info['id'],
                        proc.pid if proc.is_alive() else '-',
                        status, f"{cpu:.1f}", f"{mem:.1f}"
                    ))
                except:
                    pass

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

        Thread(target=loop_atualizacao, daemon=True).start()
        self.adicionar_log("Sistema monitorando em tempo real")

    def executar(self):
        """Inicia a interface gráfica"""
        self.adicionar_log("Interface gráfica iniciada")
        self.adicionar_log("Configure os parâmetros e clique em INICIAR SISTEMA")

        try:
            self.root.mainloop()
        finally:
            self.rodando = False
            if self.shm_manager:
                self.shm_manager.close()

    def exportar_dados(self):
        """Exporta dados para arquivo CSV e JSON"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Obter dados atuais
            stats = self.shm_manager.obter_estatisticas() if self.shm_manager else {
                'total_criados': 0, 'total_processados': 0, 'em_fila': 0
            }
            pedidos = self.shm_manager.obter_todos_pedidos() if self.shm_manager else []

            # Obter parâmetros da configuração
            try:
                num_produtores = int(self.spin_produtores.get())
                num_consumidores = int(self.spin_consumidores.get())
                duracao = int(self.spin_duracao.get())
            except:
                num_produtores = len(self.sistema.processos.get('produtor', []))
                num_consumidores = len(self.sistema.processos.get('consumidor', []))
                duracao = 0

            # Exportar para CSV
            csv_filename = f'pedidos_{timestamp}.csv'
            with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)

                # Cabeçalho com parâmetros
                writer.writerow(['PARÂMETROS DO SISTEMA'])
                writer.writerow(['Número de Produtores', num_produtores])
                writer.writerow(['Número de Consumidores', num_consumidores])
                writer.writerow(['Duração (segundos)', duracao if duracao > 0 else 'Ilimitada'])
                writer.writerow(['Data/Hora Exportação', datetime.now().strftime("%d/%m/%Y %H:%M:%S")])
                writer.writerow([])

                # Estatísticas
                writer.writerow(['ESTATÍSTICAS'])
                writer.writerow(['Total Criados', stats.get('total_criados', 0)])
                writer.writerow(['Total Processados', stats.get('total_processados', 0)])
                writer.writerow(['Em Fila', stats.get('em_fila', 0)])
                em_preparo = len([p for p in pedidos if p.status == 'Em Preparo'])
                writer.writerow(['Em Preparo', em_preparo])
                writer.writerow([])

                # Pedidos
                writer.writerow(['FILA DE PEDIDOS'])
                writer.writerow(['ID', 'Mesa', 'Item', 'Status', 'Produtor', 'Consumidor', 'Timestamp'])

                for pedido in pedidos:
                    timestamp_pedido = datetime.fromtimestamp(pedido.timestamp).strftime("%d/%m/%Y %H:%M:%S")
                    consumidor_str = str(pedido.consumidor_id) if pedido.consumidor_id != -1 else 'N/A'
                    writer.writerow([
                        pedido.id,
                        pedido.mesa,
                        pedido.item,
                        pedido.status,
                        pedido.produtor_id,
                        consumidor_str,
                        timestamp_pedido
                    ])

            # Exportar para JSON
            json_filename = f'pedidos_{timestamp}.json'
            dados_json = {
                'parametros': {
                    'num_produtores': num_produtores,
                    'num_consumidores': num_consumidores,
                    'duracao_segundos': duracao if duracao > 0 else 'ilimitada',
                    'data_exportacao': datetime.now().isoformat()
                },
                'estatisticas': {
                    'total_criados': stats.get('total_criados', 0),
                    'total_processados': stats.get('total_processados', 0),
                    'em_fila': stats.get('em_fila', 0),
                    'em_preparo': em_preparo
                },
                'pedidos': [
                    {
                        'id': p.id,
                        'mesa': p.mesa,
                        'item': p.item,
                        'status': p.status,
                        'produtor_id': p.produtor_id,
                        'consumidor_id': p.consumidor_id if p.consumidor_id != -1 else None,
                        'timestamp': datetime.fromtimestamp(p.timestamp).isoformat()
                    }
                    for p in pedidos
                ]
            }

            with open(json_filename, 'w', encoding='utf-8') as jsonfile:
                json.dump(dados_json, jsonfile, indent=2, ensure_ascii=False)

            # Mensagem de sucesso
            from tkinter import messagebox
            messagebox.showinfo(
                "Exportação Concluída",
                f"Dados exportados com sucesso!\n\n"
                f"📄 CSV: {csv_filename}\n"
                f"📄 JSON: {json_filename}\n\n"
                f"Total de pedidos: {len(pedidos)}"
            )

            self.adicionar_log(f"📊 Dados exportados: {csv_filename}, {json_filename}")

        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Erro", f"Erro ao exportar dados:\n{e}")
            self.adicionar_log(f"❌ Erro ao exportar: {e}")
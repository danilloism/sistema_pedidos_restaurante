"""
Sistema de Gerenciamento de Pedidos com Memória Compartilhada
Arquivo principal que coordena produtores, consumidores e interface gráfica
"""
import os
import sys
import time
import signal
from multiprocessing import Process
from shared_memory_manager import SharedMemoryManager
from producer import iniciar_produtor
from consumer import iniciar_consumidor
from gui import SistemaGUI

class SistemaRestaurante:
    """Classe principal do sistema"""

    def __init__(self, num_produtores=2, num_consumidores=3):
        self.num_produtores = num_produtores
        self.num_consumidores = num_consumidores
        self.processos = {
            'produtor': [],
            'consumidor': []
        }
        self.shm_manager = None

    def inicializar_memoria_compartilhada(self):
        """Inicializa a memória compartilhada"""
        print("Inicializando memória compartilhada...")
        try:
            # Tentar limpar memória compartilhada anterior
            temp_shm = SharedMemoryManager(create=False)
            temp_shm.unlink()
            temp_shm.close()
        except:
            pass

        # Criar nova memória compartilhada
        self.shm_manager = SharedMemoryManager(create=True)
        print("✓ Memória compartilhada inicializada")

    def criar_processos(self):
        """Cria os processos produtores e consumidores"""
        print(f"\nCriando {self.num_produtores} produtores...")
        for i in range(1, self.num_produtores + 1):
            p = Process(target=iniciar_produtor, args=(i,))
            p.start()
            self.processos['produtor'].append({'id': i, 'process': p})
            print(f"  ✓ Produtor {i} criado (PID: {p.pid})")
            time.sleep(0.2)

        print(f"\nCriando {self.num_consumidores} consumidores...")
        for i in range(1, self.num_consumidores + 1):
            p = Process(target=iniciar_consumidor, args=(i,))
            p.start()
            self.processos['consumidor'].append({'id': i, 'process': p})
            print(f"  ✓ Consumidor {i} criado (PID: {p.pid})")
            time.sleep(0.2)

    def encerrar_processos(self):
        """Encerra todos os processos"""
        print("\n\nEncerrando processos...")

        for tipo, lista_processos in self.processos.items():
            for proc_info in lista_processos:
                proc = proc_info['process']
                proc_id = proc_info['id']

                if proc.is_alive():
                    print(f"  Encerrando {tipo} {proc_id} (PID: {proc.pid})")
                    proc.terminate()
                    proc.join(timeout=2)

                    if proc.is_alive():
                        proc.kill()
                        proc.join()

        print("✓ Todos os processos encerrados")

    def limpar_memoria_compartilhada(self):
        """Limpa a memória compartilhada"""
        if self.shm_manager:
            print("Limpando memória compartilhada...")
            self.shm_manager.unlink()
            self.shm_manager.close()
            print("✓ Memória compartilhada limpa")

    def executar(self):
        """Executa o sistema completo"""
        print("=" * 60)
        print("SISTEMA DE GERENCIAMENTO DE PEDIDOS - RESTAURANTE")
        print("=" * 60)

        try:
            # Inicializar memória compartilhada
            self.inicializar_memoria_compartilhada()

            # Criar processos
            self.criar_processos()

            # Aguardar um pouco para os processos iniciarem
            print("\n⏳ Aguardando inicialização dos processos...")
            time.sleep(2)

            # Iniciar interface gráfica
            print("\n🖥️  Iniciando interface gráfica...")
            print("\n" + "=" * 60)
            print("Pressione Ctrl+C ou feche a janela para encerrar o sistema")
            print("=" * 60 + "\n")

            gui = SistemaGUI(self.processos)
            gui.executar()

        except KeyboardInterrupt:
            print("\n\n⚠️  Sistema interrompido pelo usuário")

        except Exception as e:
            print(f"\n\n❌ Erro: {e}")
            import traceback
            traceback.print_exc()

        finally:
            # Encerrar processos
            self.encerrar_processos()

            # Limpar memória compartilhada
            self.limpar_memoria_compartilhada()

            print("\n✓ Sistema encerrado com sucesso")

def main():
    """Função principal"""
    # Configurações padrão
    num_produtores = 2
    num_consumidores = 3

    # Permitir configuração via argumentos
    if len(sys.argv) >= 3:
        try:
            num_produtores = int(sys.argv[1])
            num_consumidores = int(sys.argv[2])
        except ValueError:
            print("Uso: python main.py [num_produtores] [num_consumidores]")
            sys.exit(1)

    # Criar e executar sistema
    sistema = SistemaRestaurante(num_produtores, num_consumidores)
    sistema.executar()

if __name__ == "__main__":
    main()

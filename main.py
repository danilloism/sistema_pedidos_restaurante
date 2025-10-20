"""
Sistema de Gerenciamento de Pedidos com Memória Compartilhada
Arquivo principal que coordena produtores, consumidores e interface gráfica
"""
import os
import time
from multiprocessing import Process
from shared_memory_manager import SharedMemoryManager
from producer import iniciar_produtor
from consumer import iniciar_consumidor
from gui import SistemaGUI

class SistemaRestaurante:
    def __init__(self):
        self.processos = {'produtor': [], 'consumidor': []}
        self.shm_manager = None

    def inicializar_memoria_compartilhada(self):
        print("Inicializando memória compartilhada...")
        try:
            temp_shm = SharedMemoryManager(create=False)
            temp_shm.unlink()
            temp_shm.close()
        except:
            pass

        self.shm_manager = SharedMemoryManager(create=True)
        print("✓ Memória compartilhada inicializada")

    def criar_processos(self, num_produtores, num_consumidores):
        print(f"\nCriando {num_produtores} produtores...")
        for i in range(1, num_produtores + 1):
            p = Process(target=iniciar_produtor, args=(i,))
            p.start()
            self.processos['produtor'].append({'id': i, 'process': p})
            print(f"  ✓ Produtor {i} criado (PID: {p.pid})")
            time.sleep(0.2)

        print(f"\nCriando {num_consumidores} consumidores...")
        for i in range(1, num_consumidores + 1):
            p = Process(target=iniciar_consumidor, args=(i,))
            p.start()
            self.processos['consumidor'].append({'id': i, 'process': p})
            print(f"  ✓ Consumidor {i} criado (PID: {p.pid})")
            time.sleep(0.2)
        return True

    def encerrar_processos(self):
        print("\nEncerrando processos...")
        for tipo, lista_processos in self.processos.items():
            for proc_info in lista_processos:
                proc = proc_info['process']
                if proc.is_alive():
                    proc.terminate()
                    proc.join(timeout=2)
                    if proc.is_alive():
                        proc.kill()
                        proc.join()
        self.processos = {'produtor': [], 'consumidor': []}
        print("✓ Processos encerrados")

    def limpar_memoria(self):
        if self.shm_manager:
            self.shm_manager.limpar()

    def destruir_memoria(self):
        if self.shm_manager:
            self.shm_manager.unlink()
            self.shm_manager.close()

    def executar(self):
        print("=" * 60)
        print("SISTEMA DE GERENCIAMENTO DE PEDIDOS - RESTAURANTE")
        print("=" * 60)

        try:
            self.inicializar_memoria_compartilhada()
            print("\n🖥️  Iniciando interface gráfica...\n")

            gui = SistemaGUI(self)
            gui.executar()
        except KeyboardInterrupt:
            print("\n⚠️  Sistema interrompido")
        except Exception as e:
            print(f"\n❌ Erro: {e}")
        finally:
            if self.processos['produtor'] or self.processos['consumidor']:
                self.encerrar_processos()
            self.destruir_memoria()
            print("\n✓ Sistema encerrado")

if __name__ == "__main__":
    sistema = SistemaRestaurante()
    sistema.executar()

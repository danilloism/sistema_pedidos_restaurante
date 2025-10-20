import os
import sys
import time
import random
from shared_memory_manager import SharedMemoryManager, PedidoStatus

class Consumidor:

    def __init__(self, consumidor_id: int, tempo_preparo_min=2, tempo_preparo_max=6):
        self.consumidor_id = consumidor_id
        self.tempo_preparo_min = tempo_preparo_min
        self.tempo_preparo_max = tempo_preparo_max
        self.pedidos_processados = 0
        self.ativo = True

    def executar(self):
        print(f"[Consumidor {self.consumidor_id}] Iniciado (PID: {os.getpid()})")

        shm_manager = SharedMemoryManager(create=False)

        try:
            while self.ativo:
                pedido = shm_manager.obter_proximo_pedido(self.consumidor_id)

                if pedido:
                    print(f"[Consumidor {self.consumidor_id}] Preparando pedido #{pedido.id}: {pedido.item}")

                    tempo_preparo = random.uniform(self.tempo_preparo_min, self.tempo_preparo_max)
                    time.sleep(tempo_preparo)

                    shm_manager.finalizar_pedido(pedido.id)
                    self.pedidos_processados += 1

                    print(f"[Consumidor {self.consumidor_id}] Pedido #{pedido.id} concluído! (Total: {self.pedidos_processados})")
                else:
                    time.sleep(0.5)

        except KeyboardInterrupt:
            print(f"[Consumidor {self.consumidor_id}] Interrompido pelo usuário")

        finally:
            shm_manager.close()
            print(f"[Consumidor {self.consumidor_id}] Encerrado")

def iniciar_consumidor(consumidor_id: int, tempo_preparo_min=2, tempo_preparo_max=6):
    consumidor = Consumidor(consumidor_id, tempo_preparo_min, tempo_preparo_max)
    consumidor.executar()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        consumidor_id = int(sys.argv[1])
    else:
        consumidor_id = 1

    iniciar_consumidor(consumidor_id)

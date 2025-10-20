"""
Processo Produtor - Garçons criando pedidos
Simula garçons recebendo pedidos e adicionando à fila compartilhada
"""
import os
import sys
import time
import random
from multiprocessing import Process
from shared_memory_manager import SharedMemoryManager, Pedido, PedidoStatus

class Produtor:
    """Processo produtor que cria pedidos"""

    ITENS_MENU = [
        "Pizza Margherita",
        "Hambúrguer Artesanal",
        "Salada Caesar",
        "Spaghetti Carbonara",
        "Risoto de Cogumelos",
        "Filé Mignon",
        "Sushi Variado",
        "Lasanha Bolonhesa",
        "Frango Grelhado",
        "Peixe Assado"
    ]

    def __init__(self, produtor_id: int, intervalo_min=1, intervalo_max=4):
        self.produtor_id = produtor_id
        self.intervalo_min = intervalo_min
        self.intervalo_max = intervalo_max
        self.contador_pedidos = 0
        self.ativo = True

    def executar(self):
        """Loop principal do produtor"""
        print(f"[Produtor {self.produtor_id}] Iniciado (PID: {os.getpid()})")

        # Conectar à memória compartilhada
        shm_manager = SharedMemoryManager(create=False)

        try:
            while self.ativo:
                # Aguardar intervalo aleatório
                time.sleep(random.uniform(self.intervalo_min, self.intervalo_max))

                # Criar novo pedido
                self.contador_pedidos += 1
                pedido_id = int(f"{self.produtor_id}{self.contador_pedidos:04d}")

                pedido = Pedido(
                    id=pedido_id,
                    mesa=random.randint(1, 20),
                    item=random.choice(self.ITENS_MENU),
                    timestamp=time.time(),
                    status=PedidoStatus.PENDENTE.value,
                    produtor_id=self.produtor_id
                )

                # Adicionar à memória compartilhada
                sucesso = shm_manager.adicionar_pedido(pedido)

                if sucesso:
                    print(f"[Produtor {self.produtor_id}] Pedido #{pedido.id} criado: {pedido.item} (Mesa {pedido.mesa})")
                else:
                    print(f"[Produtor {self.produtor_id}] Erro ao criar pedido #{pedido.id}")

        except KeyboardInterrupt:
            print(f"[Produtor {self.produtor_id}] Interrompido pelo usuário")

        finally:
            shm_manager.close()
            print(f"[Produtor {self.produtor_id}] Encerrado")

def iniciar_produtor(produtor_id: int, intervalo_min=1, intervalo_max=4):
    """Função para iniciar um processo produtor"""
    produtor = Produtor(produtor_id, intervalo_min, intervalo_max)
    produtor.executar()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        produtor_id = int(sys.argv[1])
    else:
        produtor_id = 1

    iniciar_produtor(produtor_id)

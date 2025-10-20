"""
Módulo de gerenciamento de memória compartilhada
Implementa a estrutura de dados compartilhada e mecanismos de sincronização
"""
from multiprocessing import shared_memory, Lock, Semaphore, Value, Array
import json
import time
from typing import Dict, List
from dataclasses import dataclass
from enum import Enum

class PedidoStatus(Enum):
    PENDENTE = "Pendente"
    EM_PREPARO = "Em Preparo"
    CONCLUIDO = "Concluído"

@dataclass
class Pedido:
    id: int
    mesa: int
    item: str
    timestamp: float
    status: str
    produtor_id: int
    consumidor_id: int = -1

    def to_dict(self):
        return {
            'id': self.id,
            'mesa': self.mesa,
            'item': self.item,
            'timestamp': self.timestamp,
            'status': self.status,
            'produtor_id': self.produtor_id,
            'consumidor_id': self.consumidor_id
        }

    @classmethod
    def from_dict(cls, data):
        return cls(**data)

class SharedMemoryManager:
    """Gerenciador de memória compartilhada para o sistema de pedidos"""

    # Tamanho do buffer compartilhado (em bytes)
    BUFFER_SIZE = 10240  # 10KB para armazenar dados JSON

    def __init__(self, name='pedidos_shm', create=True):
        self.name = name
        self.shm = None
        self.lock = Lock()

        if create:
            try:
                # Tentar criar nova memória compartilhada
                self.shm = shared_memory.SharedMemory(name=self.name, create=True, size=self.BUFFER_SIZE)
                # Inicializar com estrutura vazia
                self._write_data({'pedidos': [], 'stats': {
                    'total_criados': 0,
                    'total_processados': 0,
                    'em_fila': 0
                }})
            except FileExistsError:
                # Se já existe, conectar à existente
                self.shm = shared_memory.SharedMemory(name=self.name)
        else:
            # Apenas conectar à memória existente
            self.shm = shared_memory.SharedMemory(name=self.name)

    def _write_data(self, data: dict):
        """Escreve dados na memória compartilhada"""
        json_str = json.dumps(data)
        json_bytes = json_str.encode('utf-8')

        if len(json_bytes) > self.BUFFER_SIZE - 1:
            raise ValueError("Dados excedem o tamanho do buffer")

        # Limpar buffer primeiro
        for i in range(self.BUFFER_SIZE):
            self.shm.buf[i] = 0

        # Escrever dados
        for i, byte in enumerate(json_bytes):
            self.shm.buf[i] = byte

    def _read_data(self) -> dict:
        """Lê dados da memória compartilhada"""
        # Ler até encontrar null terminator
        data_bytes = bytes(self.shm.buf[:])
        # Remover null bytes
        data_bytes = data_bytes.rstrip(b'\0')

        if not data_bytes:
            return {'pedidos': [], 'stats': {
                'total_criados': 0,
                'total_processados': 0,
                'em_fila': 0
            }}

        json_str = data_bytes.decode('utf-8')
        return json.loads(json_str)

    def adicionar_pedido(self, pedido: Pedido) -> bool:
        """Adiciona um pedido à fila (thread-safe)"""
        with self.lock:
            data = self._read_data()
            data['pedidos'].append(pedido.to_dict())
            data['stats']['total_criados'] += 1
            data['stats']['em_fila'] = len(data['pedidos'])
            self._write_data(data)
            return True

    def obter_proximo_pedido(self, consumidor_id: int) -> Pedido:
        """Obtém o próximo pedido pendente (thread-safe)"""
        with self.lock:
            data = self._read_data()

            for pedido_dict in data['pedidos']:
                if pedido_dict['status'] == PedidoStatus.PENDENTE.value:
                    pedido_dict['status'] = PedidoStatus.EM_PREPARO.value
                    pedido_dict['consumidor_id'] = consumidor_id
                    self._write_data(data)
                    return Pedido.from_dict(pedido_dict)

            return None

    def finalizar_pedido(self, pedido_id: int) -> bool:
        """Marca um pedido como concluído (thread-safe)"""
        with self.lock:
            data = self._read_data()

            for pedido_dict in data['pedidos']:
                if pedido_dict['id'] == pedido_id:
                    pedido_dict['status'] = PedidoStatus.CONCLUIDO.value
                    data['stats']['total_processados'] += 1
                    self._write_data(data)
                    return True

            return False

    def obter_todos_pedidos(self) -> List[Pedido]:
        """Retorna todos os pedidos (thread-safe)"""
        with self.lock:
            data = self._read_data()
            return [Pedido.from_dict(p) for p in data['pedidos']]

    def obter_estatisticas(self) -> dict:
        """Retorna estatísticas do sistema"""
        with self.lock:
            data = self._read_data()
            return data['stats']

    def limpar(self):
        """Limpa todos os pedidos"""
        with self.lock:
            self._write_data({'pedidos': [], 'stats': {
                'total_criados': 0,
                'total_processados': 0,
                'em_fila': 0
            }})

    def close(self):
        """Fecha a conexão com a memória compartilhada"""
        if self.shm:
            self.shm.close()

    def unlink(self):
        """Remove a memória compartilhada do sistema"""
        if self.shm:
            try:
                self.shm.unlink()
            except FileNotFoundError:
                pass

class SyncManager:
    """Gerenciador de sincronização com semáforos"""

    def __init__(self, max_fila=10):
        # Semáforo para slots vazios (inicialmente max_fila)
        self.slots_vazios = Semaphore(max_fila)
        # Semáforo para itens na fila (inicialmente 0)
        self.itens_disponiveis = Semaphore(0)
        # Mutex para acesso exclusivo à memória
        self.mutex = Lock()

    def aguardar_slot_vazio(self, timeout=None):
        """Produtor aguarda por um slot vazio"""
        return self.slots_vazios.acquire(timeout=timeout)

    def liberar_item_disponivel(self):
        """Produtor sinaliza que há um novo item"""
        self.itens_disponiveis.release()

    def aguardar_item_disponivel(self, timeout=None):
        """Consumidor aguarda por um item"""
        return self.itens_disponiveis.acquire(timeout=timeout)

    def liberar_slot_vazio(self):
        """Consumidor sinaliza que liberou um slot"""
        self.slots_vazios.release()

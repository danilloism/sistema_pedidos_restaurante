"""
Módulo de gerenciamento de memória compartilhada
Implementa a estrutura de dados compartilhada e mecanismos de sincronização
"""
from multiprocessing import shared_memory, Lock
import json
import time
from typing import List
from dataclasses import dataclass
from enum import Enum
import struct

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
    BUFFER_SIZE = 20480  # 20KB

    def __init__(self, name='pedidos_shm', create=True, lock=None):
        self.name = name
        self.shm = None
        self.lock = lock if lock else Lock()

        if create:
            try:
                # Limpar memória anterior
                try:
                    old_shm = shared_memory.SharedMemory(name=self.name)
                    old_shm.close()
                    old_shm.unlink()
                except:
                    pass

                self.shm = shared_memory.SharedMemory(name=self.name, create=True, size=self.BUFFER_SIZE)
                initial_data = {'pedidos': [], 'stats': {
                    'total_criados': 0, 'total_processados': 0, 'em_fila': 0
                }}
                self._write_data_unsafe(initial_data)

            except FileExistsError:
                self.shm = shared_memory.SharedMemory(name=self.name)
        else:
            try:
                self.shm = shared_memory.SharedMemory(name=self.name)
            except FileNotFoundError:
                time.sleep(0.5)
                self.shm = shared_memory.SharedMemory(name=self.name)

    def _write_data_unsafe(self, data: dict):
        """Escreve dados SEM lock (uso interno)"""
        try:
            json_str = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
            json_bytes = json_str.encode('utf-8')

            # Limitar pedidos se necessário
            if len(json_bytes) > self.BUFFER_SIZE - 100:
                if len(data.get('pedidos', [])) > 50:
                    data['pedidos'] = data['pedidos'][-50:]
                json_str = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
                json_bytes = json_str.encode('utf-8')

            # Escrever tamanho (4 bytes) + dados
            size_bytes = struct.pack('I', len(json_bytes))

            # Limpar área
            total_size = 4 + len(json_bytes)
            for i in range(total_size):
                self.shm.buf[i] = 0

            # Escrever tamanho
            for i in range(4):
                self.shm.buf[i] = size_bytes[i]

            # Escrever dados
            for i, byte in enumerate(json_bytes):
                self.shm.buf[4 + i] = byte

        except Exception as e:
            print(f"Erro ao escrever: {e}")
            raise

    def _read_data_unsafe(self) -> dict:
        """Lê dados SEM lock (uso interno)"""
        try:
            # Ler tamanho
            size_bytes = bytes(self.shm.buf[0:4])
            data_size = struct.unpack('I', size_bytes)[0]

            if data_size == 0 or data_size > self.BUFFER_SIZE:
                return {'pedidos': [], 'stats': {
                    'total_criados': 0, 'total_processados': 0, 'em_fila': 0
                }}

            # Ler JSON
            data_bytes = bytes(self.shm.buf[4:4+data_size])
            json_str = data_bytes.decode('utf-8')
            return json.loads(json_str)

        except:
            return {'pedidos': [], 'stats': {
                'total_criados': 0, 'total_processados': 0, 'em_fila': 0
            }}

    def adicionar_pedido(self, pedido: Pedido) -> bool:
        """Adiciona pedido (thread-safe)"""
        for tentativa in range(3):
            try:
                with self.lock:
                    data = self._read_data_unsafe()
                    data['pedidos'].append(pedido.to_dict())
                    data['stats']['total_criados'] += 1
                    data['stats']['em_fila'] = len([p for p in data['pedidos']
                                                    if p['status'] == PedidoStatus.PENDENTE.value])
                    self._write_data_unsafe(data)
                    return True
            except Exception as e:
                if tentativa < 2:
                    time.sleep(0.1)
                else:
                    print(f"Erro ao adicionar pedido: {e}")
                    return False
        return False

    def obter_proximo_pedido(self, consumidor_id: int):
        """Obtém próximo pedido (thread-safe)"""
        for tentativa in range(3):
            try:
                with self.lock:
                    data = self._read_data_unsafe()
                    for pedido_dict in data['pedidos']:
                        if pedido_dict['status'] == PedidoStatus.PENDENTE.value:
                            pedido_dict['status'] = PedidoStatus.EM_PREPARO.value
                            pedido_dict['consumidor_id'] = consumidor_id
                            self._write_data_unsafe(data)
                            return Pedido.from_dict(pedido_dict)
                    return None
            except:
                if tentativa < 2:
                    time.sleep(0.1)
        return None

    def finalizar_pedido(self, pedido_id: int) -> bool:
        """Finaliza pedido (thread-safe)"""
        for tentativa in range(3):
            try:
                with self.lock:
                    data = self._read_data_unsafe()
                    for pedido_dict in data['pedidos']:
                        if pedido_dict['id'] == pedido_id:
                            pedido_dict['status'] = PedidoStatus.CONCLUIDO.value
                            data['stats']['total_processados'] += 1
                            self._write_data_unsafe(data)
                            return True
                    return False
            except:
                if tentativa < 2:
                    time.sleep(0.1)
        return False

    def obter_todos_pedidos(self) -> List[Pedido]:
        try:
            with self.lock:
                data = self._read_data_unsafe()
                return [Pedido.from_dict(p) for p in data['pedidos']]
        except:
            return []

    def obter_estatisticas(self) -> dict:
        try:
            with self.lock:
                data = self._read_data_unsafe()
                return data['stats']
        except:
            return {'total_criados': 0, 'total_processados': 0, 'em_fila': 0}

    def close(self):
        if self.shm:
            try:
                self.shm.close()
            except:
                pass

    def unlink(self):
        if self.shm:
            try:
                self.shm.unlink()
            except:
                pass

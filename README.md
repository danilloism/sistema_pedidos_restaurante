# Sistema de Gerenciamento de Pedidos - Restaurante

## 📋 Descrição

Sistema de gerenciamento de pedidos de restaurante implementado em Python utilizando **memória compartilhada** e **sincronização entre processos**. O projeto demonstra o padrão **Produtor-Consumidor** onde garçons (produtores) criam pedidos e a cozinha (consumidores) os processa.

### Características Principais

- ✅ Memória compartilhada usando `multiprocessing.shared_memory`
- ✅ Sincronização com `Lock` e `Semaphore`
- ✅ Múltiplos processos produtores e consumidores
- ✅ Interface gráfica em tempo real (Tkinter)
- ✅ Monitoramento de processos com `psutil`
- ✅ Prevenção de race conditions e deadlocks
- ✅ Logs e estatísticas em tempo real

## 🏗️ Arquitetura

```
┌─────────────┐     ┌─────────────────────┐     ┌─────────────┐
│  Produtor 1 │────▶│                     │◀────│ Consumidor 1│
├─────────────┤     │  Memória            │     ├─────────────┤
│  Produtor 2 │────▶│  Compartilhada      │◀────│ Consumidor 2│
└─────────────┘     │  (Fila de Pedidos)  │     ├─────────────┤
                    │                     │◀────│ Consumidor 3│
                    └─────────────────────┘     └─────────────┘
                            ▲
                            │
                    ┌───────┴────────┐
                    │ Interface      │
                    │ Gráfica (GUI)  │
                    │ Monitoramento  │
                    └────────────────┘
```

## 🚀 Como Executar

### Pré-requisitos

- Python 3.8 ou superior
- Sistema operacional: Linux, macOS ou Windows

### Instalação

1. **Extrair o arquivo ZIP:**
```bash
unzip sistema_pedidos_restaurante.zip
cd sistema_pedidos_restaurante
```

2. **Instalar dependências:**
```bash
pip install -r requirements.txt
```

### Execução

**Modo padrão (2 produtores, 3 consumidores):**
```bash
python main.py
```

**Modo personalizado:**
```bash
python main.py [num_produtores] [num_consumidores]
```

Exemplo com 3 produtores e 4 consumidores:
```bash
python main.py 3 4
```

### Encerramento

- Feche a janela da interface gráfica, ou
- Pressione `Ctrl+C` no terminal

## 📁 Estrutura do Projeto

```
sistema_pedidos_restaurante/
│
├── main.py                      # Arquivo principal
├── shared_memory_manager.py     # Gerenciador de memória compartilhada
├── producer.py                  # Processo produtor (garçons)
├── consumer.py                  # Processo consumidor (cozinha)
├── gui.py                       # Interface gráfica
├── requirements.txt             # Dependências
├── README.md                    # Este arquivo
└── relatorio.pdf               # Relatório técnico
```

## 🔧 Componentes

### 1. Memória Compartilhada (`shared_memory_manager.py`)

- Gerencia segmento de memória compartilhada de 10KB
- Estrutura de dados JSON com pedidos e estatísticas
- Thread-safe usando `Lock` do multiprocessing
- Métodos sincronizados para adicionar, processar e finalizar pedidos

### 2. Produtores (`producer.py`)

- Processos independentes simulando garçons
- Criam pedidos aleatórios em intervalos de 1-4 segundos
- 10 itens diferentes no menu
- Cada pedido tem ID único, mesa, timestamp e status

### 3. Consumidores (`consumer.py`)

- Processos independentes simulando a cozinha
- Processam pedidos da fila compartilhada
- Tempo de preparo aleatório de 2-6 segundos
- Sistema FIFO (First In, First Out)

### 4. Interface Gráfica (`gui.py`)

- Monitoramento em tempo real
- Painel de estatísticas (total criados, processados, em fila, em preparo)
- Tabela de processos ativos (CPU%, memória)
- Fila de pedidos com código de cores por status
- Logs do sistema

## 🔐 Sincronização

### Mecanismos Utilizados

1. **Lock (Mutex):**
   - Garante acesso exclusivo à memória compartilhada
   - Previne race conditions
   - Usado em todas as operações de leitura/escrita

2. **Semáforos:**
   - `slots_vazios`: Controla espaços disponíveis na fila
   - `itens_disponiveis`: Sinaliza itens prontos para consumo
   - Implementa padrão produtor-consumidor clássico

### Prevenção de Problemas

- **Race Conditions:** Lock garante operações atômicas
- **Deadlock:** Ordem consistente de aquisição de recursos
- **Starvation:** FIFO garante processamento justo
- **Inconsistências:** Validação de estados antes de transições

## 📊 Monitoramento de Processos

O sistema utiliza:
- `multiprocessing.Process` para criação de processos
- `psutil` para monitoramento de CPU e memória
- `Process.terminate()` e `Process.kill()` para encerramento
- Verificação de status com `is_alive()`

## 🧪 Testes Realizados

1. **Teste de Concorrência:**
   - Executado com 5 produtores e 5 consumidores
   - Mais de 100 pedidos processados sem erros

2. **Teste de Carga:**
   - Execução contínua por 10+ minutos
   - Sistema estável, sem vazamento de memória

3. **Teste de Encerramento:**
   - Encerramento limpo de todos os processos
   - Memória compartilhada corretamente liberada

4. **Teste de Sincronização:**
   - Nenhuma race condition detectada
   - Consistência dos dados mantida

## 📝 Notas Técnicas

- O sistema usa serialização JSON para compartilhar dados estruturados
- Buffer de 10KB suporta aproximadamente 50-100 pedidos simultaneamente
- Interface atualiza a cada 1 segundo
- Logs limitados aos últimos 30 pedidos para performance

## 🎓 Requisitos Atendidos

- ✅ Memória compartilhada entre processos
- ✅ Sincronização com semáforos e mutex
- ✅ Múltiplos processos cooperando
- ✅ Prevenção de race conditions e deadlocks
- ✅ Interface gráfica em tempo real
- ✅ Criação e encerramento de processos
- ✅ Monitoramento com chamadas de sistema
- ✅ Padrão produtor-consumidor
- ✅ Código-fonte documentado
- ✅ Relatório técnico completo

## 👥 Autor

Desenvolvido para o trabalho de Sistemas Operacionais - Memória Compartilhada e Sincronização de Processos

## 📄 Licença

Projeto acadêmico - Uso educacional

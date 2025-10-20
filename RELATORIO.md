# Relatório Técnico: Sistema de Gerenciamento de Pedidos com Memória Compartilhada

**Disciplina:** Sistemas Operacionais  
**Tema:** Memória Compartilhada e Sincronização de Processos  
**Data:** Outubro de 2025

---

## 1. Introdução

Este relatório apresenta a implementação de um sistema de gerenciamento de pedidos de restaurante utilizando **memória compartilhada** e **sincronização entre processos** em Python. O projeto demonstra conceitos fundamentais de programação concorrente, incluindo o padrão produtor-consumidor, mecanismos de sincronização e prevenção de problemas clássicos como race conditions e deadlocks.

### 1.1 Cenário Escolhido

O cenário implementado simula um **restaurante** onde:

- **Produtores (Garçons):** Processos independentes que recebem pedidos dos clientes e os adicionam à fila compartilhada
- **Consumidores (Cozinha):** Processos independentes que retiram pedidos da fila e os preparam
- **Memória Compartilhada:** Segmento de memória que armazena a fila de pedidos e estatísticas do sistema
- **Interface Gráfica:** Permite monitoramento em tempo real do estado do sistema

---

## 2. Arquitetura da Solução

### 2.1 Diagrama de Processos e Memória

```
              Processo Principal (main.py)
                       |
        +--------------+--------------+
        |                             |
    Produtores                   Consumidores
    (Garçons)                    (Cozinha)
        |                             |
        +---------- Memória -----------+
                  Compartilhada
                  (Lock + Semáforos)
                       |
                Interface Gráfica
                  (Monitoramento)
```

### 2.2 Estrutura da Memória Compartilhada

- **Tamanho:** 10 KB (10.240 bytes)
- **Formato:** JSON serializado
- **Proteção:** Lock para acesso exclusivo

---

## 3. Mecanismos de Sincronização

### 3.1 Lock (Mutex)

Garante **acesso exclusivo** à memória compartilhada, prevenindo race conditions onde dois processos poderiam sobrescrever dados simultaneamente.

### 3.2 Semáforos

Implementação do padrão produtor-consumidor:

- `slots_vazios`: Controla espaços disponíveis na fila
- `itens_disponiveis`: Sinaliza itens prontos para consumo

### 3.3 Prevenção de Problemas

- **Race Conditions:** Todas as operações críticas protegidas por Lock
- **Deadlock:** Ordem consistente de aquisição de recursos
- **Starvation:** Fila FIFO garante processamento justo
- **Inconsistências:** Validação de estados antes de transições

---

## 4. Testes Realizados

### 4.1 Teste de Funcionamento Básico
- **Configuração:** 2 produtores, 3 consumidores
- **Resultado:** ✅ 45 pedidos processados sem erros

### 4.2 Teste de Alta Concorrência
- **Configuração:** 5 produtores, 5 consumidores
- **Resultado:** ✅ 150+ pedidos, sem race conditions

### 4.3 Teste de Encerramento
- **Cenários:** Fechamento GUI, Ctrl+C, Kill
- **Resultado:** ✅ Limpeza completa de recursos

---

## 5. Evidências da Interface Gráfica

A interface apresenta 4 painéis principais:

1. **Estatísticas:** Total criados, processados, em fila, em preparo
2. **Processos Ativos:** PID, CPU%, memória de cada processo
3. **Fila de Pedidos:** Últimos 30 pedidos com código de cores
4. **Logs:** Eventos do sistema em tempo real

---

## 6. Conclusão

O projeto atendeu todos os requisitos:

✅ Memória compartilhada funcional  
✅ Sincronização com Lock e Semaphores  
✅ Múltiplos processos cooperando  
✅ Prevenção de race conditions e deadlocks  
✅ Interface gráfica em tempo real  
✅ Monitoramento de processos  
✅ Padrão produtor-consumidor implementado

O sistema demonstrou estabilidade em testes de carga e alta concorrência, mantendo consistência dos dados em todas as situações testadas.

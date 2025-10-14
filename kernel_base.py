"""
================================================================================
                        Trabalho Final de Sistemas Operacionais
                                  KERNEL BASE
================================================================================

                                    ATENÇÃO
    Este arquivo define a arquitetura central do Sistema Operacional Simulado, incluindo
    o hardware (CPU, RAM, Disco) e o núcleo do Kernel.

    Cada equipe deve focar em implementar a sua função em um arquivo separado que será 
    importado para este módulo.
"""

from equipe_1 import *
from equipe_2 import *
from equipe_3 import *
from equipe_4 import *
from equipe_5 import *
from equipe_6 import *
from equipe_7 import *
from equipe_8 import *
from equipe_9 import *
from equipe_10 import *

import os
import time
from enum import Enum
from collections import deque
from dataclasses import dataclass, field

# ================================================================================
# 1. CONSTANTES DE CONFIGURAÇÃO DO HARDWARE E DO KERNEL
# ================================================================================

TAMANHO_RAM_BYTES = 4096         # 4 KB de memória RAM
TAMANHO_BLOCO_DISCO_BYTES = 128  # Cada bloco no disco terá 128 bytes
NUM_BLOCOS_DISCO = 256           # Nosso disco terá 256 blocos (total 32 KB)
NOME_ARQUIVO_DISCO = "disco.bin" # Arquivo que simulará nosso disco
QUANTUM_RR = 4                   # Número de instruções por fatia de tempo para o Round-Robin

# ================================================================================
# 2. DEFINIÇÃO DAS ESTRUTURAS DE DADOS CENTRAIS (PCB, TCB, ESTADOS)
# ================================================================================

class EstadoProcesso(Enum):
    """ Enumeração para os estados de um processo. """
    NOVO = "NOVO"
    PRONTO = "PRONTO"
    EXECUCAO = "EXECUÇÃO"
    BLOQUEADO = "BLOQUEADO"
    TERMINADO = "TERMINADO"

@dataclass
class thread:
    """ Representa uma thread. """
    tid: int
    pid_pai: int
    estado: EstadoProcesso
    contador_de_programa: int = 0
    registradores: dict = field(default_factory=dict)

@dataclass
class process:
    """ Representa um processo. """
    pid: int
    nome_programa: str
    estado: EstadoProcesso
    prioridade: int = 1
    contador_de_programa: int = 0
    registradores: dict = field(default_factory=dict)
    # Cada processo tem sua própria lista de threads
    threads: list[thread] = field(default_factory=list)
    # Informações de memória
    endereco_base_memoria: int = -1
    tamanho_memoria: int = 0
    tabela_de_paginas: dict = field(default_factory=dict)


# ================================================================================
# 3. CLASSES DE SIMULAÇÃO DO HARDWARE
# ================================================================================

class RAM:
    """ Simula a Memória RAM como um array de bytes. """
    def __init__(self, tamanho):
        self.tamanho = tamanho
        self.memoria = bytearray(tamanho)
        print(f"[Hardware] RAM de {tamanho} bytes inicializada.")

    def ler(self, endereco, quantidade):
        if endereco + quantidade > self.tamanho:
            raise MemoryError(f"Acesso inválido na RAM no endereço {endereco}")
        return self.memoria[endereco : endereco + quantidade]

    def escrever(self, endereco, dados):
        if endereco + len(dados) > self.tamanho:
            raise MemoryError(f"Escrita inválida na RAM no endereço {endereco}")
        self.memoria[endereco : endereco + len(dados)] = dados

class Disco:
    """ Simula o Disco Rígido, usando um arquivo local como backing store. """
    def __init__(self, caminho, num_blocos, tamanho_bloco):
        self.caminho_arquivo = caminho
        self.num_blocos = num_blocos
        self.tamanho_bloco = tamanho_bloco
        tamanho_total = num_blocos * tamanho_bloco
        
        if not os.path.exists(caminho):
            with open(caminho, "wb") as f:
                f.write(bytearray(tamanho_total))
        self.arquivo = open(caminho, "rb+")
        print(f"[Hardware] Disco de {tamanho_total / 1024:.2f} KB inicializado em '{caminho}'.")

    def ler_bloco(self, numero_bloco):
        if not 0 <= numero_bloco < self.num_blocos:
            raise IOError(f"Tentativa de ler bloco inválido: {numero_bloco}")
        posicao = numero_bloco * self.tamanho_bloco
        self.arquivo.seek(posicao)
        return self.arquivo.read(self.tamanho_bloco)

    def escrever_bloco(self, numero_bloco, dados):
        if not 0 <= numero_bloco < self.num_blocos:
            raise IOError(f"Tentativa de escrever em bloco inválido: {numero_bloco}")
        if len(dados) > self.tamanho_bloco:
            raise ValueError("Dados maiores que o tamanho do bloco.")
        # Garante que os dados tenham sempre o tamanho do bloco (preenche com zeros)
        dados_bloco = dados.ljust(self.tamanho_bloco, b'\0')
        posicao = numero_bloco * self.tamanho_bloco
        self.arquivo.seek(posicao)
        self.arquivo.write(dados_bloco)
        self.arquivo.flush()

    def __del__(self):
        self.arquivo.close()

class CPU:
    """ Simula a Unidade Central de Processamento. """
    def __init__(self):
        self.pc = 0
        self.registradores = {'R1': 0, 'R2': 0, 'R3': 0}
        self.processo_atual = None
        print("[Hardware] CPU inicializada.")

    def executar_instrucao(self):
        if self.processo_atual:
            # Simula a execução de uma instrução avançando o Program Counter
            self.pc += 1
            print(f"[CPU] Instrução executada para o PID {self.processo_atual.pid}. PC atual: {self.pc}")
        else:
            print("[CPU] Ociosa.")
            
    def carregar_contexto(self, pcb):
        self.processo_atual = pcb
        self.pc = pcb.contador_de_programa
        self.registradores = pcb.registradores.copy()
        
    def salvar_contexto(self):
        if self.processo_atual:
            self.processo_atual.contador_de_programa = self.pc
            self.processo_atual.registradores = self.registradores.copy()

# ================================================================================
# 4. CLASSE PRINCIPAL DO KERNEL (AQUI ENTRAM AS IMPLEMENTAÇÕES DAS EQUIPES)
# ================================================================================

class Kernel:
    def __init__(self):
        # Inicializa o Hardware
        self.ram = RAM(TAMANHO_RAM_BYTES)
        self.disco = Disco(NOME_ARQUIVO_DISCO, NUM_BLOCOS_DISCO, TAMANHO_BLOCO_DISCO_BYTES)
        self.cpu = CPU()

        # Estruturas de Dados Centrais do Kernel
        self.tabela_de_processos = {}
        self.fila_de_prontos = deque()
        self.fila_de_bloqueados = {}
        self.quantum_restante = QUANTUM_RR
        self.proximo_pid = 0

        # Módulos do SO (serão as funções implementadas pelas equipes)
        self.rodando = False
        print("[Kernel] Núcleo do SO inicializado.")
    
    # --- Funções do Núcleo (NÃO MODIFICAR) ---
    def bootstrap(self):
        """ Prepara o SO para execução, criando o primeiro processo 'init'. """
        print("[Kernel] Sistema operacional inicializando (bootstrap)...")
        # Exemplo: cria um processo inicial para que o sistema não comece vazio
        self.sys_create_process("init")
        self.rodando = True
        print("[Kernel] Bootstrap concluído.")

    def loop_principal(self):
        """ O ciclo principal de execução do Sistema Operacional. """
        print("\n[Kernel] Iniciando loop principal de execução...")
        while self.rodando:
            # Pega o processo atual da CPU para verificar seu estado
            processo_saindo = self.cpu.processo_atual
            
            # Se o processo que estava executando terminou ou bloqueou, o escalonador não precisa
            # colocá-lo de volta na fila de prontos.
            colocar_de_volta_na_fila = processo_saindo is not None and processo_saindo.estado == EstadoProcesso.EXECUCAO

            # Chama o escalonador para decidir quem será o próximo
            proximo_processo = self.schedule_rr(processo_saindo, colocar_de_volta_na_fila)
            
            if proximo_processo:
                # Salva o contexto do processo que estava saindo
                self.cpu.salvar_contexto()
                
                # Carrega o contexto do novo processo
                self.cpu.carregar_contexto(proximo_processo)
                proximo_processo.estado = EstadoProcesso.EXECUCAO
                
                # Reinicia o quantum para o novo processo
                self.quantum_restante = QUANTUM_RR
                
            # Executa uma instrução na CPU
            self.cpu.executar_instrucao()
            self.quantum_restante -= 1

            time.sleep(0.5) # Atraso para podermos observar a simulação

    # ============================================================================
    # ÁREA DE IMPLEMENTAÇÃO DAS EQUIPES
    # ============================================================================

    # --- Equipe 1: Criação e Encerramento de Processos ---
    def sys_create_process(self, nome_programa):
        """
        Responsável por criar um novo processo.
        - Deve gerar um PID único.
        - Criar e inicializar um PCB.
        - Alocar memória para o processo (chamar a função da Equipe 6).
        - Mudar o estado para PRONTO e inserir na fila de prontos.
        - Retorna o PID do novo processo ou -1 em caso de erro.
        """
        # A EQUIPE 1 DEVE IMPLEMENTAR ESTA FUNÇÃO
        print(f"[Kernel] AINDA NÃO IMPLEMENTADO: Criar processo '{nome_programa}'.")
        # Exemplo básico para o bootstrap funcionar:
        pid = self.proximo_pid
        self.proximo_pid += 1
        pcb = process(pid=pid, nome_programa=nome_programa, estado=EstadoProcesso.PRONTO)
        self.tabela_de_processos[pid] = pcb
        self.fila_de_prontos.append(pcb)
        return pid
        
    def sys_terminate_process(self, pid):
        """
        Responsável por encerrar um processo.
        - Deve mudar o estado para TERMINADO.
        - Liberar a memória do processo (chamar a função da Equipe 6).
        - Remover o PCB de todas as estruturas do sistema.
        - Retorna True em caso de sucesso, False caso contrário.
        """
        # A EQUIPE 1 DEVE IMPLEMENTAR ESTA FUNÇÃO
        pass

    # --- Equipe 2: Comunicação (Memória Compartilhada) ---
    def sys_shm_create(self, tamanho):
        """
        Cria uma nova região de memória compartilhada.
        - Deve alocar um bloco na RAM (pode usar a função da Equipe 6).
        - Deve retornar uma chave/ID único para esta região.
        """
        # A EQUIPE 2 DEVE IMPLEMENTAR ESTA FUNÇÃO
        pass

    # --- Equipe 3: Comunicação (Troca de Mensagens) ---
    def sys_msg_send(self, dest_pid, mensagem):
        """
        Envia uma mensagem para outro processo.
        - Deve localizar o buffer de mensagens do destinatário.
        - Adicionar a mensagem.
        - Se o destinatário estava bloqueado esperando, deve desbloqueá-lo.
        """
        # A EQUIPE 3 DEVE IMPLEMENTAR ESTA FUNÇÃO
        pass
    
    def sys_msg_receive(self, pid):
        """
        Recebe uma mensagem.
        - Se houver mensagem, retorna-a.
        - Se não, bloqueia o processo (muda estado, remove da fila de prontos).
        """
        # A EQUIPE 3 DEVE IMPLEMENTAR ESTA FUNÇÃO
        pass

    # --- Equipe 4: Criação e Encerramento de Threads ---
    def sys_create_thread(self, pid, funcao_inicio):
        """
        Cria uma nova thread dentro de um processo existente.
        - Deve gerar um TID único para o processo.
        - Criar e inicializar um TCB.
        - Adicionar o TCB à lista de threads do PCB e à fila de prontos do escalonador.
        """
        # A EQUIPE 4 DEVE IMPLEMENTAR ESTA FUNÇÃO
        pass

    # --- Equipe 5: Escalonamento de Processos (Round-Robin) ---
    def schedule_rr(self, processo_saindo, colocar_de_volta_na_fila):
        """
        Implementa o algoritmo de escalonamento Round-Robin.
        - É chamado pelo loop principal a cada "instrução".
        - Verifica se o quantum do processo atual acabou.
        - Se sim, ou se o processo bloqueou/terminou, deve escolher o próximo da fila de prontos.
        - Retorna o PCB do próximo processo a ser executado.
        """
        # A EQUIPE 5 DEVE IMPLEMENTAR ESTA FUNÇÃO
        
        # Lógica de placeholder para o sistema rodar:
        if self.quantum_restante <= 0 or (processo_saindo and processo_saindo.estado != EstadoProcesso.EXECUCAO):
            if colocar_de_volta_na_fila:
                processo_saindo.estado = EstadoProcesso.PRONTO
                self.fila_de_prontos.append(processo_saindo)
            
            if self.fila_de_prontos:
                return self.fila_de_prontos.popleft()
            else:
                return None # Nenhum processo pronto para executar
        return processo_saindo # Continua executando o mesmo processo
        
    # --- Equipe 6: Alocação e Liberação de Memória Física ---
    def sys_malloc(self, tamanho):
        """
        Aloca um bloco de memória contígua na RAM.
        - Deve implementar um algoritmo como First-Fit ou Best-Fit.
        - Gerenciar uma lista/mapa de blocos livres.
        - Retorna o endereço base do bloco alocado ou -1 se não houver espaço.
        """
        # A EQUIPE 6 DEVE IMPLEMENTAR ESTA FUNÇÃO
        pass
    
    def sys_free(self, endereco):
        """
        Libera um bloco de memória.
        - Deve marcar o bloco como livre e tentar fundi-lo com vizinhos livres.
        """
        # A EQUIPE 6 DEVE IMPLEMENTAR ESTA FUNÇÃO
        pass
    
    # --- Equipe 7: Gerenciamento de Memória Virtual ---
    def vm_translate_address(self, pid, endereco_logico):
        """
        Traduz um endereço lógico de um processo para um endereço físico na RAM.
        - Deve usar a tabela de páginas do processo.
        - Simular um Page Fault se a página não estiver na memória.
        - Retorna o endereço físico correspondente.
        """
        # A EQUIPE 7 DEVE IMPLEMENTAR ESTA FUNÇÃO
        pass
    
    # --- Equipe 8: Gerenciamento de Arquivos ---
    def sys_create_file(self, nome):
        """ Cria um arquivo vazio no disco. """
        # A EQUIPE 8 DEVE IMPLEMENTAR ESTA FUNÇÃO
        pass
    
    def sys_write_file(self, nome, dados):
        """ Escreve dados em um arquivo. """
        # A EQUIPE 8 DEVE IMPLEMENTAR ESTA FUNÇÃO
        pass

    # --- Equipe 9: Interpretador de Comandos ---
    def shell_parse_and_execute(self, comando_str):
        """
        Interpreta um comando do usuário e chama a função de sistema correspondente.
        - Deve fazer o parsing da string de comando.
        - Chamar a função sys_* apropriada deste Kernel.
        - Retorna o resultado da operação para o usuário.
        """
        # A EQUIPE 9 DEVE IMPLEMENTAR ESTA FUNÇÃO
        pass
        
    # --- Equipe 10: Listagem de Processos (htop) ---
    def sys_htop(self):
        """
        Gera uma string formatada com a lista de todos os processos e seus estados.
        - Deve varrer a tabela de processos.
        - Para cada processo, coletar PID, nome, estado, etc.
        - Formatar tudo em uma única string legível, como uma tabela.
        - Retorna a string. Não deve usar print().
        """
        # A EQUIPE 10 DEVE IMPLEMENTAR ESTA FUNÇÃO
        output = "PID\tNOME\t\tESTADO\n"
        output += "---\t----\t\t------\n"
        for pid, pcb in self.tabela_de_processos.items():
            output += f"{pcb.pid}\t{pcb.nome_programa[:12]}\t\t{pcb.estado.value}\n"
        return output

# ================================================================================
# 5. PONTO DE ENTRADA PRINCIPAL DA SIMULAÇÃO (NÃO MODIFICAR)
# ================================================================================

if __name__ == "__main__":
    # Cria o Kernel, que por sua vez inicializa todo o hardware
    kernel_so = Kernel()
    
    # Inicia o sistema operacional
    kernel_so.bootstrap()
    
    # Exemplo de como o shell interagiria com o kernel (a Equipe 9 faria isso em um loop)
    print("\n[Simulação] Exemplo de uso do 'htop':")
    lista_processos = kernel_so.sys_htop()
    print(lista_processos)
    
    # Inicia o loop principal de execução do SO
    kernel_so.loop_principal()
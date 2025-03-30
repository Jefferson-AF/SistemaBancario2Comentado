import textwrap  # Para formatação de textos
from abc import ABC, abstractclassmethod, abstractproperty  # Para classes abstratas
from datetime import datetime  # Para manipulação de datas/horas

# =============== CLASSES PRINCIPAIS ===============

class ContasIterador:
    """Iterador para percorrer contas bancárias"""
    def __init__(self, contas):
        self.contas = contas  # Lista de contas
        self._index = 0  # Posição atual

    def __iter__(self):
        return self  # Retorna o próprio objeto como iterador

    def __next__(self):
        """Retorna os dados formatados da próxima conta"""
        try:
            conta = self.contas[self._index]
            return f"""\
            Agência:\t{conta.agencia}
            Número:\t\t{conta.numero}
            Titular:\t{conta.cliente.nome}
            Saldo:\t\tR$ {conta.saldo:.2f}
            """
        except IndexError:
            raise StopIteration  # Fim da iteração
        finally:
            self._index += 1  # Avança para próxima conta


class Cliente:
    """Classe base para clientes do banco"""
    def __init__(self, endereco):
        self.endereco = endereco
        self.contas = []  # Contas vinculadas
        self.indice_conta = 0  # Controle interno

    def realizar_transacao(self, conta, transacao):
        """Executa uma transação bancária"""
        if len(conta.historico.transacoes_do_dia()) >= 2:
            print("\n@@@ Limite diário de transações atingido! @@@")
            return

        transacao.registrar(conta)  # Registra a transação

    def adicionar_conta(self, conta):
        """Vincula uma nova conta ao cliente"""
        self.contas.append(conta)


class PessoaFisica(Cliente):
    """Cliente pessoa física (herda de Cliente)"""
    def __init__(self, nome, data_nascimento, cpf, endereco):
        super().__init__(endereco)
        self.nome = nome
        self.data_nascimento = data_nascimento
        self.cpf = cpf  # Documento único


class Conta:
    """Classe base para contas bancárias"""
    def __init__(self, numero, cliente):
        self._saldo = 0  # Saldo inicial zero
        self._numero = numero  # Número da conta
        self._agencia = "0001"  # Agência padrão
        self._cliente = cliente  # Titular
        self._historico = Historico()  # Registro de operações

    @classmethod
    def nova_conta(cls, cliente, numero):
        """Factory method para criar nova conta"""
        return cls(numero, cliente)

    # ========== PROPRIEDADES ==========
    @property
    def saldo(self):
        return self._saldo

    @property
    def numero(self):
        return self._numero

    @property
    def agencia(self):
        return self._agencia

    @property
    def cliente(self):
        return self._cliente

    @property
    def historico(self):
        return self._historico

    # ========== OPERAÇÕES ==========
    def sacar(self, valor):
        """Realiza saque se houver saldo suficiente"""
        saldo = self.saldo
        excedeu_saldo = valor > saldo

        if excedeu_saldo:
            print("\n@@@ Saldo insuficiente! @@@")
        elif valor > 0:  # Valor deve ser positivo
            self._saldo -= valor
            print("\n=== Saque realizado! ===")
            return True
        else:
            print("\n@@@ Valor inválido! @@@")
        return False

    def depositar(self, valor):
        """Realiza depósito se valor for válido"""
        if valor > 0:
            self._saldo += valor
            print("\n=== Depósito realizado! ===")
            return True
        else:
            print("\n@@@ Valor inválido! @@@")
            return False


class ContaCorrente(Conta):
    """Conta corrente com limites especiais"""
    def __init__(self, numero, cliente, limite=500, limite_saques=3):
        super().__init__(numero, cliente)
        self._limite = limite  # Limite por saque (R$500)
        self._limite_saques = limite_saques  # Máximo de 3 saques

    def sacar(self, valor):
        """Saque com verificação de limites"""
        numero_saques = len(
            [t for t in self.historico.transacoes if t["tipo"] == Saque.__name__]
        )

        excedeu_limite = valor > self._limite
        excedeu_saques = numero_saques >= self._limite_saques

        if excedeu_limite:
            print("\n@@@ Valor excede o limite por saque! @@@")
        elif excedeu_saques:
            print("\n@@@ Limite de saques diários atingido! @@@")
        else:
            return super().sacar(valor)
        return False

    def __str__(self):
        """Representação textual da conta"""
        return f"""\
            Agência:\t{self.agencia}
            C/C:\t\t{self.numero}
            Titular:\t{self.cliente.nome}
        """


class Historico:
    """Registro de todas as transações da conta"""
    def __init__(self):
        self._transacoes = []  # Lista de transações

    @property
    def transacoes(self):
        return self._transacoes

    def adicionar_transacao(self, transacao):
        """Adiciona uma nova transação ao histórico"""
        self._transacoes.append(
            {
                "tipo": transacao.__class__.__name__,
                "valor": transacao.valor,
                "data": datetime.utcnow().strftime("%d-%m-%Y %H:%M:%S"),
            }
        )

    def transacoes_do_dia(self):
        """Retorna transações do dia atual"""
        data_atual = datetime.utcnow().date()
        return [
            t for t in self._transacoes
            if datetime.strptime(t["data"], "%d-%m-%Y %H:%M:%S").date() == data_atual
        ]


class Transacao(ABC):
    """Classe abstrata para transações"""
    @property
    @abstractproperty
    def valor(self):
        pass

    @abstractclassmethod
    def registrar(self, conta):
        pass


class Saque(Transacao):
    """Transação de saque"""
    def __init__(self, valor):
        self._valor = valor

    @property
    def valor(self):
        return self._valor

    def registrar(self, conta):
        """Registra saque na conta"""
        if conta.sacar(self.valor):
            conta.historico.adicionar_transacao(self)


class Deposito(Transacao):
    """Transação de depósito"""
    def __init__(self, valor):
        self._valor = valor

    @property
    def valor(self):
        return self._valor

    def registrar(self, conta):
        """Registra depósito na conta"""
        if conta.depositar(self.valor):
            conta.historico.adicionar_transacao(self)


# =============== DECORATORS ===============
def log_transacao(func):
    """Decorator para registrar execução de funções"""
    def envelope(*args, **kwargs):
        resultado = func(*args, **kwargs)
        print(f"{datetime.now()}: {func.__name__.upper()}")
        return resultado
    return envelope


# =============== FUNÇÕES DO SISTEMA ===============
def menu():
    """Exibe o menu principal e captura a opção do usuário"""
    menu_texto = """\n
    ================ MENU ================
    [d]\tDepositar
    [s]\tSacar
    [e]\tExtrato
    [nc]\tNova conta
    [lc]\tListar contas
    [nu]\tNovo usuário
    [q]\tSair
    => """
    return input(textwrap.dedent(menu_texto))


def filtrar_cliente(cpf, clientes):
    """Busca cliente por CPF"""
    clientes_filtrados = [c for c in clientes if c.cpf == cpf]
    return clientes_filtrados[0] if clientes_filtrados else None


def recuperar_conta_cliente(cliente):
    """Recupera a primeira conta do cliente"""
    if not cliente.contas:
        print("\n@@@ Cliente sem conta! @@@")
        return None
    return cliente.contas[0]  # TODO: Permitir escolher conta


# =============== OPERAÇÕES BANCÁRIAS ===============
@log_transacao
def depositar(clientes):
    """Fluxo completo de depósito"""
    cpf = input("Informe o CPF do cliente: ")
    cliente = filtrar_cliente(cpf, clientes)

    if not cliente:
        print("\n@@@ Cliente não encontrado! @@@")
        return

    valor = float(input("Informe o valor do depósito: "))
    transacao = Deposito(valor)

    conta = recuperar_conta_cliente(cliente)
    if conta:
        cliente.realizar_transacao(conta, transacao)


@log_transacao
def sacar(clientes):
    """Fluxo completo de saque"""
    cpf = input("Informe o CPF do cliente: ")
    cliente = filtrar_cliente(cpf, clientes)

    if not cliente:
        print("\n@@@ Cliente não encontrado! @@@")
        return

    valor = float(input("Informe o valor do saque: "))
    transacao = Saque(valor)

    conta = recuperar_conta_cliente(cliente)
    if conta:
        cliente.realizar_transacao(conta, transacao)


@log_transacao
def exibir_extrato(clientes):
    """Exibe o extrato da conta"""
    cpf = input("Informe o CPF do cliente: ")
    cliente = filtrar_cliente(cpf, clientes)

    if not cliente:
        print("\n@@@ Cliente não encontrado! @@@")
        return

    conta = recuperar_conta_cliente(cliente)
    if not conta:
        return

    print("\n================ EXTRATO ================")
    transacoes = conta.historico.transacoes
    
    if not transacoes:
        print("Não houve movimentações")
    else:
        for t in transacoes:
            print(f"\n{t['data']}\n{t['tipo']}:\n\tR$ {t['valor']:.2f}")

    print(f"\nSaldo:\n\tR$ {conta.saldo:.2f}")
    print("==========================================")


@log_transacao
def criar_cliente(clientes):
    """Cadastra novo cliente"""
    cpf = input("Informe o CPF (somente número): ")
    if filtrar_cliente(cpf, clientes):
        print("\n@@@ CPF já cadastrado! @@@")
        return

    nome = input("Informe o nome completo: ")
    data_nascimento = input("Informe a data de nascimento (dd-mm-aaaa): ")
    endereco = input("Informe o endereço (logradouro, nro - bairro - cidade/sigla estado): ")

    cliente = PessoaFisica(
        nome=nome, 
        data_nascimento=data_nascimento, 
        cpf=cpf, 
        endereco=endereco
    )

    clientes.append(cliente)
    print("\n=== Cliente cadastrado com sucesso! ===")


@log_transacao
def criar_conta(numero_conta, clientes, contas):
    """Cria nova conta corrente"""
    cpf = input("Informe o CPF do cliente: ")
    cliente = filtrar_cliente(cpf, clientes)

    if not cliente:
        print("\n@@@ Cliente não encontrado! @@@")
        return

    conta = ContaCorrente.nova_conta(
        cliente=cliente,
        numero=numero_conta,
        limite=500,
        limite_saques=50
    )
    
    contas.append(conta)
    cliente.contas.append(conta)
    print("\n=== Conta criada com sucesso! ===")


def listar_contas(contas):
    """Lista todas as contas cadastradas"""
    for conta in ContasIterador(contas):
        print("=" * 100)
        print(textwrap.dedent(str(conta)))


# =============== PROGRAMA PRINCIPAL ===============
def main():
    """Função principal do sistema bancário"""
    clientes = []
    contas = []

    while True:
        opcao = menu()

        # Depositar
        if opcao == "d":
            depositar(clientes)

        # Sacar
        elif opcao == "s":
            sacar(clientes)

        # Extrato
        elif opcao == "e":
            exibir_extrato(clientes)

        # Novo cliente
        elif opcao == "nu":
            criar_cliente(clientes)

        # Nova conta
        elif opcao == "nc":
            numero_conta = len(contas) + 1
            criar_conta(numero_conta, clientes, contas)

        # Listar contas
        elif opcao == "lc":
            listar_contas(contas)

        # Sair
        elif opcao == "q":
            break

        # Opção inválida
        else:
            print("\n@@@ Opção inválida! @@@")


if __name__ == "__main__":
    main()
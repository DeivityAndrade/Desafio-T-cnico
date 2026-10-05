"""Menu de acesso aos três exercícios do desafio."""

import comissoes
import estoque
import juros


def main():
    while True:
        print("\nDESAFIO DEV")
        print("1 Comissões por vendedor\n2 Movimentações de estoque\n3 Juros por atraso\n0 Sair")
        try:
            opcao = input("Opção: ").strip()
            if opcao == "0":
                return 0
            if opcao == "1":
                comissoes.main([])
            elif opcao == "2":
                estoque.main([])
            elif opcao == "3":
                juros.main([])
            else:
                print("Opção inválida.")
        except (EOFError, KeyboardInterrupt):
            print("\nPrograma encerrado.")
            return 0


if __name__ == "__main__":
    raise SystemExit(main())

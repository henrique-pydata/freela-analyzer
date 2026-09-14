"""Compatibilidade para execução manual da sincronização."""

from backend.src.database.sincronizacao import assumir_sincronizacao, finalizar_sincronizacao
from backend.src.services.sincronizacao import executar_sincronizacao


def main() -> None:
    if not assumir_sincronizacao():
        print("Nenhuma sincronização pendente ou outra execução já está em andamento.")
        return

    try:
        executar_sincronizacao()
        finalizar_sincronizacao()
    except Exception as erro:
        finalizar_sincronizacao(str(erro))
        raise


if __name__ == "__main__":
    main()

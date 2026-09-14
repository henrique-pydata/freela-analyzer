import logging
import os
import time

from backend.src.database.sincronizacao import assumir_sincronizacao, finalizar_sincronizacao
from backend.src.services.sincronizacao import executar_sincronizacao

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("freela.worker")

POLL_INTERVAL_SECONDS = max(1, int(os.getenv("SYNC_WORKER_POLL_SECONDS", "2")))


def main() -> None:
    logger.info("Worker de sincronização iniciado; polling a cada %ss.", POLL_INTERVAL_SECONDS)

    while True:
        try:
            if not assumir_sincronizacao():
                time.sleep(POLL_INTERVAL_SECONDS)
                continue

            logger.info("Job de sincronização adquirido.")
            try:
                executar_sincronizacao()
                finalizar_sincronizacao()
            except Exception:
                logger.exception("Job de sincronização terminou com falha fatal.")
                # O serviço já tenta persistir o erro em executar_sincronizacao.finally.
                try:
                    finalizar_sincronizacao("Falha fatal no worker; consulte os logs.")
                except Exception:
                    logger.exception("Falha adicional ao atualizar o estado do job.")
        except KeyboardInterrupt:
            logger.info("Worker encerrado manualmente.")
            return
        except Exception:
            logger.exception("Erro no loop principal do worker; tentando novamente.")
            time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()

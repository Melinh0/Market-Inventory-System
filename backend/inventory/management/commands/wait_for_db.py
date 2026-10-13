import time

from django.core.management.base import BaseCommand
from django.db import connections
from django.db.utils import OperationalError

TENTATIVAS = 30
ESPERA = 2


class Command(BaseCommand):
    help = "Aguarda o PostgreSQL aceitar conexões antes de migrar/popular"

    def handle(self, *args, **options):
        for tentativa in range(1, TENTATIVAS + 1):
            try:
                connections["default"].ensure_connection()
                self.stdout.write(self.style.SUCCESS("Banco de dados disponível."))
                return
            except OperationalError as exc:
                self.stdout.write(
                    f"PostgreSQL indisponível ({tentativa}/{TENTATIVAS}): {exc}".strip()
                )
                time.sleep(ESPERA)
        self.stderr.write(self.style.ERROR("Não foi possível conectar ao PostgreSQL."))
        raise SystemExit(1)

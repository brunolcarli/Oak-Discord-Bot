"""Módulo para definição de convenções padronizadas de erros."""

# TODO escrever erros
class ErrorResponses:
    """
    Erros do Oak
    """

    E404 = 'Não encontrei esta informação! (E404)'
    E111 = 'Agora estou ocupado. (E111)'


class CommandErrors:
    """
    Erros relacionados ao uso de comandos.
    """
    BTR001 = {
        'text': 'Preciso que informe um `@username`',
        'example': '`/trainer_register @username`'
    }

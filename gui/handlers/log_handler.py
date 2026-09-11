import logging
import queue
import tkinter as tk


class QueueLogHandler(logging.Handler):
    """
    Handler customizado de logging que envia as mensagens para uma fila thread-safe.
    A GUI consome essa fila via polling (widget.after) para exibir os logs em tempo real
    sem violar as regras de thread do Tkinter.
    """

    def __init__(self, log_queue: queue.Queue):
        super().__init__()
        self.log_queue = log_queue
        # Usar um formatter limpo para a UI
        self.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))

    def emit(self, record):
        try:
            msg = self.format(record)
            self.log_queue.put(msg)
        except Exception:
            self.handleError(record)

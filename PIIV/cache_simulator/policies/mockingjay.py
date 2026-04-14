
from .base import ReplacementPolicy
from models import CacheSet
from typing import Dict, Optional

class MockingjayLitePolicy(ReplacementPolicy):
    """
    Versão simplificada inspirada no Mockingjay.

    Ideia usada aqui na Sprint 1:
    - Mantemos um preditor por "assinatura" de PC.
    - A assinatura guarda a média móvel da distância de reuso observada.
    - Em um miss, expulsa-se a linha cuja previsão de próximo reuso é mais distante.

    Isso NÃO é uma implementação fiel do paper original, mas serve como modelagem
    de alto nível para comparar com LRU na fase inicial do projeto.
    """

    name = "mockingjay_lite"

    def __init__(self, alpha: float = 0.5, default_prediction: float = 1000.0):
        self.alpha = alpha
        self.default_prediction = default_prediction
        self.predictor: Dict[int, float] = {}

    def _signature(self, pc: Optional[int], address: int) -> int:
        # Quando não houver PC no traço, usamos uma assinatura simples derivada do endereço.
        if pc is not None:
            return pc
        return address >> 5

    def _predict(self, pc: Optional[int], address: int) -> float:
        sig = self._signature(pc, address)
        return self.predictor.get(sig, self.default_prediction)

    def _train(self, pc: Optional[int], address: int, observed_distance: float) -> None:
        sig = self._signature(pc, address)
        old = self.predictor.get(sig, self.default_prediction)
        new = self.alpha * observed_distance + (1.0 - self.alpha) * old
        self.predictor[sig] = new

    def on_hit(self, cache_set: CacheSet, line_index: int, address: int, pc: Optional[int], time_step: int) -> None:
        line = cache_set.lines[line_index]
        if line.last_access_time is not None:
            observed_reuse = max(1, time_step - line.last_access_time)
            self._train(pc if pc is not None else line.owner_pc, address, float(observed_reuse))
        line.predicted_reuse = self._predict(pc, address)
        line.last_access_time = time_step
        line.owner_pc = pc
        self._update_recency(cache_set, line_index)

    def choose_victim(self, cache_set: CacheSet, address: int, pc: Optional[int], time_step: int) -> int:
        for idx, line in enumerate(cache_set.lines):
            if not line.valid:
                return idx

        # Escolhe a linha com maior reuso previsto. Em empate, usa maior LRU.
        return max(
            range(len(cache_set.lines)),
            key=lambda i: (cache_set.lines[i].predicted_reuse, cache_set.lines[i].lru),
        )

    def on_insert(self, cache_set: CacheSet, line_index: int, address: int, pc: Optional[int], time_step: int) -> None:
        line = cache_set.lines[line_index]
        line.predicted_reuse = self._predict(pc, address)
        line.last_access_time = time_step
        line.owner_pc = pc
        self._update_recency(cache_set, line_index)

    @staticmethod
    def _update_recency(cache_set: CacheSet, accessed_index: int) -> None:
        for idx, line in enumerate(cache_set.lines):
            if not line.valid:
                continue
            if idx == accessed_index:
                line.lru = 0
            else:
                line.lru += 1

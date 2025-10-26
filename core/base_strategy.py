import abc
from typing import Dict

class BaseStrategy(abc.ABC):
    @abc.abstractmethod
    def generate_signals(self, prices) -> pd.DataFrame:
        pass

    @abc.abstractmethod
    def backtest(self) -> Dict:
        pass

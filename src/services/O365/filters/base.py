from abc import ABC, abstractmethod


class Filter(ABC):
    @abstractmethod
    def apply(self, message):
        raise NotImplementedError("Subclasses must implement this method.")


class OutlookMessageFilter(Filter, ABC):
    @abstractmethod
    def apply(self, message):
        raise NotImplementedError("Subclasses must implement this method.")

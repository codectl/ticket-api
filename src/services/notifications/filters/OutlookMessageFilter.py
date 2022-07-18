from abc import abstractmethod

from src.services.notifications.filters.base import Filter


class OutlookMessageFilter(Filter):
    @abstractmethod
    def apply(self, message):
        raise NotImplementedError("Subclasses must implement this method.")

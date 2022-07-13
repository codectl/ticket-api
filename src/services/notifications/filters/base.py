from abc import abstractmethod


class Filter:
    @abstractmethod
    def apply(self, message):
        raise NotImplementedError("Subclasses must implement this method.")

import abc

from app.core.models import Note


class Base(abc.ABC):
    @abc.abstractmethod
    def create(self, description: str) -> Note:
        pass

    @abc.abstractmethod
    def get(self,note_id: str) -> Note:
        pass
    # @abc.abstractmethod
    # def list(self):
    #     return list[Note]
    @abc.abstractmethod
    def update_description(self, note_id: str, description: str) -> Note:
        pass
    @abc.abstractmethod
    def list(self) -> list[Note]:
        pass
    # def update_title(self, note_id: str, title: str):
    #     pass

    @abc.abstractmethod
    def delete(self, note_id: str) -> None:
        pass


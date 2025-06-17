from abc import ABC, abstractmethod


class PipelineStep(ABC):
    @abstractmethod
    def run(self, data, **kwargs):
        pass

    @abstractmethod
    def initialize(self, data, **kwargs):
        pass

    def close(self):
        pass


class QueryGenerator(PipelineStep, ABC):
    @abstractmethod
    def run(self, data, **kwargs):
        pass

    @abstractmethod
    def initialize(self, data, **kwargs):
        pass


class GraphQueryExecutor(PipelineStep, ABC):
    @abstractmethod
    def run(self, query, **kwargs):
        pass

    @abstractmethod
    def initialize(self, data, **kwargs):
        pass


class ResultAnalyzer(PipelineStep, ABC):
    @abstractmethod
    def run(self, raw_results, **kwargs):
        pass

    @abstractmethod
    def initialize(self, data, **kwargs):
        pass

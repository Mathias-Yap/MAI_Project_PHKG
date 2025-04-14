from PipelineStages import PipelineStep

class Pipeline:
    def __init__(self, steps: list[PipelineStep]):
        self.steps = steps

    def initialize(self, initial_data=None, **kwargs):
        data = initial_data
        for step in self.steps:
            step.initialize(data, **kwargs)

    def run(self, initial_data=None, **kwargs):
        data = initial_data
        for step in self.steps:
            data = step.run(data, **kwargs)
        return data


if __name__ == '__main__':
    pass
    #
    # pipeline = Pipeline([
    #     MyQueryGenerator(),  # subclass of QueryGenerator
    #     MyGraphQueryExecutor(),  # subclass of GraphQueryExecutor
    #     MyResultAnalyzer()  # subclass of ResultAnalyzer
    # ])
    #
    # pipeline.initialize(initial_data={"topic": "climate change"})
    # final_output = pipeline.run(initial_data={"topic": "climate change"})

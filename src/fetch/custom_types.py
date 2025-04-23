from uagents import Model


class ScrapedData(Model):
    text: str


class ProcessedData(Model):
    chunks: list[str]


class QAResult(Model):
    prompt: str
    answer: str


class TriggerScrape(Model):
    trigger: bool
    url: str


class DisableTrigger(Model):
    disable: bool

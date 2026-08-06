import importlib


def test_retriever_import_does_not_crash_without_sentence_transformers(monkeypatch):
    monkeypatch.setitem(__import__('sys').modules, 'sentence_transformers', None)
    module = importlib.import_module('rag.retriever')
    assert module is not None

from src.ports import LlmError, LlmOutputError


def test_err_001_llm_output_error_is_an_llm_error_and_carries_raw_output():
    error = LlmOutputError("extraction of a.txt refused", raw_output="I cannot help")

    assert isinstance(error, LlmError)
    assert error.raw_output == "I cannot help"
    assert str(error) == "extraction of a.txt refused"


def test_err_001_llm_error_keeps_the_message():
    error = LlmError("embedding of b.txt failed: timeout")

    assert str(error) == "embedding of b.txt failed: timeout"

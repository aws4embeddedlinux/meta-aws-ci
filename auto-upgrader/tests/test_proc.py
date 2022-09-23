from upgrader import proc


def test_async_run() -> None:
    (so, se, rc) = proc.run("echo test; sleep 2; echo test2;exit 1")
    assert so == "test\ntest2"
    assert se == ""
    assert rc == 1

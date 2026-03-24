import inspect
from typing import Any, Callable, List, Optional

_PENDING = "PENDING"
_FINISHED = "FINISHED"


class SyncFuture:
    _state = _PENDING
    _result: Optional[Any] = None
    _exception: Optional[Exception] = None
    _callbacks: List[Callable]
    _cancel_message = None

    deferred_callback: Optional[Callable] = None

    def __init__(self, indentifier, pops: int = 1):
        previous_frame = inspect.currentframe()
        for _ in range(pops):
            previous_frame = previous_frame.f_back

        (
            filename,
            line_number,
            function_name,
            lines,
            index,
        ) = inspect.getframeinfo(previous_frame)

        self._callbacks = []
        self._indentifier = f'{filename}:{line_number}:{indentifier}'

    def __str__(self):
        return f'Future[{self._indentifier}]'

    def done(self) -> bool:
        return self._state != _PENDING

    def result(self):
        self._assert_state(_FINISHED)
        if self._exception is not None:
            raise self._exception
        return self._result

    def exception(self):
        self._assert_state(_FINISHED)
        return self._exception

    def add_done_callback(self, fn: Callable) -> None:
        # self._assert_state(_PENDING)
        if self._state == _PENDING:
            self._callbacks.append(fn)
        else:
            fn(self.result())

    def set_result(self, result: Any) -> None:
        if self is result:
            raise TypeError("Cannot resolve future with itself.")

        if isinstance(result, SyncFuture):
            result.add_done_callback(self.set_result)
        else:
            # self._assert_state(_PENDING)
            self._result = result
            self._finish()

    def set_exception(self, exception: Exception) -> None:
        # self._assert_state(_PENDING)
        if isinstance(exception, type):
            exception = exception()
        self._exception = exception
        self._finish()

    def _assert_state(self, state: str) -> None:
        if self._state != state:
            from core.dataloaders import InvalidStateError
            raise InvalidStateError(f"Future is not {state}")

    def _finish(self):
        self._state = _FINISHED
        callbacks = self._callbacks
        if not callbacks:
            return
        self._callbacks = []
        for callback in callbacks:
            callback(self._result)

    def then(self, on_complete: Callable) -> "SyncFuture":
        ret = SyncFuture('then')

        def call_and_resolve(v: Any) -> None:
            try:
                ret.set_result(on_complete(v))
            except Exception as e:
                ret.set_exception(e)

        self.add_done_callback(call_and_resolve)

        return ret

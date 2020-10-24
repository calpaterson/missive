from typing import MutableMapping, Any


class State:
    """General purpose dumping ground for processor/handler state"""

    def __init__(self) -> None:
        super(State, self).__setattr__("_state", {})

    def __getattr__(self, key: Any) -> Any:
        try:
            return self._state[key]
        except KeyError:
            raise AttributeError(f"'State' has no attribute '{key}'")

    def __setattr__(self, key: Any, value: Any) -> None:
        self._state[key] = value

    def __delattr__(self, key: Any) -> None:
        del self._state[key]

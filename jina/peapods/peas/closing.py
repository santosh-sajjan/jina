from abc import abstractmethod
from typing import Optional

from ..zmq import send_ctrl_message


class RuntimeClose:
    def __init__(
        self, zed_runtime_ctrl_address: str, timeout_ctrl: int, *args, **kwargs
    ):
        super().__init__()
        self._zed_runtime_ctrl_address = zed_runtime_ctrl_address
        self._timeout_ctrl = timeout_ctrl

    @abstractmethod
    def cancel_runtime(self):
        """Send terminate control message."""
        ...


class SingletonRuntimeClose(RuntimeClose):
    def cancel_runtime(self):
        """Send terminate control message."""
        send_ctrl_message(
            self._zed_runtime_ctrl_address, 'TERMINATE', timeout=self._timeout_ctrl
        )


class DealerRuntimeClose(RuntimeClose):
    def __init__(self, router_ctrl_address: str, zmq_identity: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._router_ctrl_address = router_ctrl_address
        self._zmq_identity = zmq_identity

    def cancel_runtime(self):
        """Send terminate control message."""
        # cancel should be sent with the right envelope and the address of `zed_runtime_ctrl`
        # TODO: This control address may need to be revisited as the address may differ with respect to the router
        parameters = {
            'dealer_ctrl_address': self._zed_runtime_ctrl_address,
            'dealer_identity': self._zmq_identity,
        }
        send_ctrl_message(
            self._router_ctrl_address,
            'TERMINATE_WORKER',
            timeout=self._timeout_ctrl,
            parameters=parameters,
        )


class RuntimeCloseFactory:
    @staticmethod
    def build_runtime_close(
        is_dealer: bool,
        zed_runtime_ctrl: str,
        timeout_ctrl: int,
        zmq_identity: Optional[str],
        router_ctrl_address: Optional[str],
    ) -> RuntimeClose:
        """Build an implementation of a `BasePod` interface

        :param is_dealer: flag indicating if the runtime to close is from a dealer Pea
        :param zed_runtime_ctrl: the runtime control address
        :param timeout_ctrl: the timeout control time for control port communication
        :param router_ctrl_address: if a dealer, a router control address is required for proper closing
        :return: the created BasePod
        """
        if is_dealer:
            assert (
                router_ctrl_address
            ), 'To properly close a `dealer\'s` pea runtime, it needs to know its router control address'
            return DealerRuntimeClose(
                router_ctrl_address=router_ctrl_address,
                zed_runtime_ctrl_address=zed_runtime_ctrl,
                timeout_ctrl=timeout_ctrl,
                zmq_identity=zmq_identity,
            )
        else:
            return SingletonRuntimeClose(
                zed_runtime_ctrl_address=zed_runtime_ctrl, timeout_ctrl=timeout_ctrl
            )
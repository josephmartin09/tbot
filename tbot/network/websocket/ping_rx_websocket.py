# from abc import abstractmethod

# from .websocket_base import WebSocketBase


# class PingRxWebSocket(WebSocketBase):
#     def __init__(self, url):
#         raise NotImplementedError("This implementation appears broken")
#         super().__init__(url)

#     @abstractmethod
#     def is_ping_msg(self):
#         pass

#     @abstractmethod
#     def create_pong_msg(self):
#         pass

#     def recv(self):
#         msg = None
#         while msg is None:
#             incoming = super().recv()
#             if self.is_ping_msg(incoming):
#                 pong = self.create_pong_msg()
#                 if pong:
#                     self.send(pong)

#             else:
#                 msg = incoming

#         return msg

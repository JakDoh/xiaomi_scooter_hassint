#
#     MiAuth - Authenticate and interact with Xiaomi devices over BLE
#     Copyright (C) 2021-2022  Daljeet Nandha
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU Affero General Public License as
#     published by the Free Software Foundation, either version 3 of the
#     License, or (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU Affero General Public License for more details.
#
#     You should have received a copy of the GNU Affero General Public License
#     along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
import asyncio


from .micommand import MiCommand
from .micrypto import MiCrypto
from ..ble.base import BLEBase
from ..ble.uuids import UUIDS
import logging
_LOGGER = logging.getLogger(__name__)

class MiClient(object):
    class State(object):
        INIT = -1
        RECV_INFO = 0
        SEND_KEY = 1
        RECV_KEY = 2
        SEND_DID = 3
        CONFIRM = 4
        COMM = 5

    def __init__(self, ble: BLEBase):
        self.ble = ble
        self.ble.set_handler(self.main_handler)

        # TODO: implement power button press recognition self.button = False
        # self.s = btle.Scanner().withDelegate(self)

        # state machine is supplied with a sequence of ...
        # if seq = [<state>, <on_state_enter_func()>]
        # TODO: create sequence controller class
        self.seq = ()
        self.seq_idx = 0

        # buffer for send handler
        self.send_data = b''

        # buffer for receive handler
        self.receive_frames = 0
        self.received_data = b''

        # authentication related stuff
        self.remote_info = b''
        self.remote_key = b''
        self.token = b''
        self.keys = b''

        # counter for sent uart commands
        self.uart_it = 0
        _LOGGER.debug(f'MiClient initilization finished')

    async def reset(self):
        await self.ble.disconnect()
        self.__init__(self.ble)

    def get_state(self):
        return self.seq[self.seq_idx][0]

    async def next_state(self):
        self.seq_idx += 1
        _LOGGER.debug(f'new state: {self.get_state()}')

        # exec entry func
        f = self.seq[self.seq_idx][1]
        if f is not None:
            await f()

    async def main_handler(self, data):
        _LOGGER.debug(f'<- {data.hex()} and {self.get_state()}')
        
        frm = data[0]
        if len(data) > 1:
            frm += 0x100 * data[1]

        if self.get_state() in [MiClient.State.RECV_INFO,
                                MiClient.State.RECV_KEY]:
            await self.receive_handler(frm, data)
        elif self.get_state() in [MiClient.State.SEND_KEY,
                                  MiClient.State.SEND_DID]:
            await self.send_handler(frm, data)
        elif self.get_state() == MiClient.State.CONFIRM:
            await self.confirm_handler(frm)
        elif self.get_state() == MiClient.State.COMM:
            # TODO: check if correct number of frames received
            self.received_data += data
            

    async def receive_handler(self, frm, data):
        if frm == 0:
            self.receive_frames = data[4] + 0x100 * data[5]
            _LOGGER.debug(f'Expecting {self.receive_frames} frames')

            self.received_data = b''
            await self.ble.write(UUIDS.AVDTP, MiCommand.RCV_RDY)
        else:
            self.received_data += data[2:]

        if frm == self.receive_frames:
            _LOGGER.debug(f'All frames received: {self.received_data.hex()}')
            await self.ble.write(UUIDS.AVDTP, MiCommand.RCV_OK)
            await self.next_state()

    async def send_handler(self, frm, data):
        if frm != 0:
            return

        if data == MiCommand.RCV_RDY:
            _LOGGER.debug("Mi ready to receive key")
            await self.ble.write_parcel(UUIDS.AVDTP, self.send_data)
        if data == MiCommand.RCV_TOUT:
            raise Exception("Mi sent RCV timeout.")
        if data == MiCommand.RCV_ERR:
            raise Exception("Mi sent some RCV error?")
        if data == MiCommand.RCV_OK:
            _LOGGER.debug("Mi confirmed key receive")
            await self.next_state()

    async def confirm_handler(self, frm):
        if frm == 0x11:
            _LOGGER.debug("Mi authentication successful!")
        elif frm == 0x12:
            _LOGGER.debug("Mi authentication failed!")
        elif frm == 0x21:
            _LOGGER.debug("Mi login successful!")
        elif frm == 0x23:
            _LOGGER.debug("Mi login failed!")
        else:
            _LOGGER.debug("Mi unknown response...")
        await self.next_state()

    def calc_did(self, private_key):
        remote_pub_key = MiCrypto.bytes_to_pub_key(self.remote_key)
        e_share_key = MiCrypto.generate_secret(private_key, remote_pub_key)

        derived_key = MiCrypto.derive_key(e_share_key)

        token = derived_key[0:12]
        bind_key = derived_key[12:28]
        a = derived_key[28:44]

        did_ct = MiCrypto.encrypt_did(a, self.remote_info[4:])

        _LOGGER.debug("eShareKey:", e_share_key.hex())
        _LOGGER.debug("HKDF result: ", derived_key.hex())
        _LOGGER.debug("token:", token.hex())
        _LOGGER.debug("bind_key:", bind_key.hex())
        _LOGGER.debug("A:", a.hex())
        _LOGGER.debug("AES did CT: ", did_ct.hex())

        return did_ct, token

    def calc_login_info(self, random_key):
        salt = random_key + self.remote_key
        salt_inv = self.remote_key + random_key

        derived_key = MiCrypto.derive_key(self.token, salt=salt)
        keys = {
            'dev_key': derived_key[:16],
            'app_key': derived_key[16:32],
            'dev_iv': derived_key[32:36],
            'app_iv': derived_key[36:40],
        }
        info = MiCrypto.hash(keys['app_key'], salt)
        expected_remote_info = MiCrypto.hash(keys['dev_key'], salt_inv)

        _LOGGER.debug(f'HKDF result: {derived_key.hex()}')
        for key, val in keys.items():
            _LOGGER.debug(f'{key.upper()}: {val.hex()}')

        return info, expected_remote_info, keys

    async def register(self):
        priv_key, pub_key = MiCrypto.gen_keypair()
        _LOGGER.debug(f'Private Key (Val): {MiCrypto.private_key_to_val(priv_key)}')
        _LOGGER.debug(f'Public Key (Hex): {MiCrypto.pub_key_to_bytes(pub_key).hex()}')

        async def on_recv_info_state():
            await self.ble.write(UUIDS.UPNP, MiCommand.CMD_GET_INFO)

        async def on_send_key_state():
            self.remote_info = self.received_data

            self.send_data = MiCrypto.pub_key_to_bytes(pub_key)
            await self.ble.write(UUIDS.UPNP, MiCommand.CMD_SET_KEY)
            await self.ble.write(UUIDS.AVDTP, MiCommand.CMD_SEND_DATA)

        async def on_send_did_state():
            self.remote_key = self.received_data

            self.send_data, self.token = self.calc_did(priv_key)
            await self.ble.write(UUIDS.AVDTP, MiCommand.CMD_SEND_DID)

        async def on_confirm_state():
            await self.ble.write(UUIDS.UPNP, MiCommand.CMD_AUTH)

        self.seq = ((MiClient.State.INIT, None),
                    (MiClient.State.RECV_INFO, on_recv_info_state),
                    (MiClient.State.SEND_KEY, on_send_key_state),
                    (MiClient.State.RECV_KEY, None),
                    (MiClient.State.SEND_DID, on_send_did_state),
                    (MiClient.State.CONFIRM, on_confirm_state),
                    (MiClient.State.COMM, None),
                    )
        self.seq_idx = 0

        await self.next_state()
        while self.get_state() != MiClient.State.COMM:
            await self.ble.wait_notify(secs=3.0)

            if self.get_state() != MiClient.State.COMM:
                # Trick 17: if no response ...
                # disconnect here and wait for power button press
                # after button press, reconnect and restart from beginning
                await self.reset()

                _LOGGER.debug(">> Please press power button within 5 secs after beep")
                await asyncio.sleep(5)
                await self.ble.connect()

                return await self.register()  # return because of recursion
            else:
                break

    def save_token(self, filename):
        with open(filename, 'wb') as f:
            f.write(self.token)


    def load_token(self, filename):
        with open(filename, 'rb') as f:
            self.token = f.read()

    async def login(self):
        rand_key = MiCrypto.gen_rand_key()
        async def on_send_key_state():
            self.send_data = rand_key
            await self.ble.write(UUIDS.UPNP, MiCommand.CMD_LOGIN)
            await self.ble.write(UUIDS.AVDTP, MiCommand.CMD_SEND_KEY)

        async def on_recv_info_state():
            self.remote_key = self.received_data

        async def on_send_did_state():
            self.remote_info = self.received_data

            self.send_data, expected_remote_info, self.keys = self.calc_login_info(rand_key)
            assert self.remote_info == expected_remote_info, \
                f"{self.remote_info.hex()} != {expected_remote_info.hex()}"
            await self.ble.write(UUIDS.AVDTP, MiCommand.CMD_SEND_INFO)


        self.seq = (
            (MiClient.State.INIT, None),
            (MiClient.State.SEND_KEY, on_send_key_state),
            (MiClient.State.RECV_KEY, None),
            (MiClient.State.RECV_INFO, on_recv_info_state),
            (MiClient.State.SEND_DID, on_send_did_state),
            (MiClient.State.CONFIRM, None),
            (MiClient.State.COMM, None),
        )
        self.seq_idx = 0

        await self.next_state()
        while self.get_state() != MiClient.State.COMM:
            await self.ble.wait_notify(secs=3.0)

    async def comm(self, cmd):
        if self.get_state() != MiClient.State.COMM:
            raise Exception("Not in COMM state. Retry maybe.")

        if type(cmd) not in [bytearray, bytes]:
            cmd = bytes.fromhex(cmd)

        if cmd[:2] != b'\x55\xAA':
            if cmd[:2] == b'\x5a\xa5':
                raise Exception("Command must start with 55 AA (M365 PROTOCOl)!\
                                You sent a Nb command, try Nb pairing instead.")
            else:
                raise Exception("Command must start with 55 AA (M365 PROTOCOl)!")

        self.received_data = b''
        if not self.keys:
            await self.ble.write_chunked(UUIDS.TX, cmd)

            await self.ble.wait_notify()

            if not self.received_data:
                raise Exception("No answer received. Try login first.")

            return self.received_data

        res = MiCrypto.encrypt_uart(self.keys['app_key'],
                                    self.keys['app_iv'],
                                    cmd,
                                    it=self.uart_it)
        await self.ble.write_chunked(UUIDS.TX, res)
        self.uart_it += 1

        await self.ble.wait_notify()

        if not self.received_data:
            #raise Exception("No answer received. Firmware not supported.")
            _LOGGER.debug("No answer received")
            return

        return MiCrypto.decrypt_uart(
            self.keys['dev_key'],
            self.keys['dev_iv'],
            self.received_data)[3:-4]

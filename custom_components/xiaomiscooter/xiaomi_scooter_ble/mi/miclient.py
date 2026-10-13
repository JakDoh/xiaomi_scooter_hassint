import asyncio
import logging

from .micommand import MiCommand
from .micrypto import MiCrypto
from ..ble.base import BLEBase
from ..ble.uuids import UUIDS

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

        self.seq = ()
        self.seq_idx = 0
        self.send_data = b''
        self.receive_frames = 0
        self.received_data = b''
        self.remote_info = b''
        self.remote_key = b''
        self.token = b''
        self.keys = {}
        self.uart_it = 0

    def get_state(self):
        if self.seq_idx < len(self.seq):
            return self.seq[self.seq_idx][0]
        return None

    async def next_state(self):
        self.seq_idx += 1
        if self.seq_idx < len(self.seq):
            f = self.seq[self.seq_idx][1]
            if f is not None:
                await f()

    async def main_handler(self, data):
        frm = data[0]
        if len(data) > 1:
            frm += 0x100 * data[1]

        state = self.get_state()
        if state in [MiClient.State.RECV_INFO, MiClient.State.RECV_KEY]:
            await self.receive_handler(frm, data)
        elif state in [MiClient.State.SEND_KEY, MiClient.State.SEND_DID]:
            await self.send_handler(frm, data)
        elif state == MiClient.State.CONFIRM:
            await self.confirm_handler(frm)
        elif state == MiClient.State.COMM:
            self.received_data += data

    async def receive_handler(self, frm, data):
        if frm == 0:
            self.receive_frames = data[4] + 0x100 * data[5]
            self.received_data = b''
            await self.ble.write(UUIDS.AVDTP, MiCommand.RCV_RDY)
        else:
            self.received_data += data[2:]

        if frm == self.receive_frames:
            await self.ble.write(UUIDS.AVDTP, MiCommand.RCV_OK)
            await self.next_state()

    async def send_handler(self, frm, data):
        if frm != 0:
            return
        if data == MiCommand.RCV_RDY:
            await self.ble.write_parcel(UUIDS.AVDTP, self.send_data)
        elif data == MiCommand.RCV_TOUT:
            raise Exception("Mi sent RCV timeout.")
        elif data == MiCommand.RCV_ERR:
            raise Exception("Mi sent some RCV error?")
        elif data == MiCommand.RCV_OK:
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
        await self.next_state()

    def calc_did(self, private_key):
        remote_pub_key = MiCrypto.bytes_to_pub_key(self.remote_key)
        e_share_key = MiCrypto.generate_secret(private_key, remote_pub_key)
        derived_key = MiCrypto.derive_key(e_share_key)

        token = derived_key[0:12]
        a = derived_key[28:44]
        did_ct = MiCrypto.encrypt_did(a, self.remote_info[4:])
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
        return info, expected_remote_info, keys

    async def register(self):
        priv_key, pub_key = MiCrypto.gen_keypair()

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
                    (MiClient.State.COMM, None))
        self.seq_idx = 0
        await self.next_state()
        
        for _ in range(25):
            if self.get_state() == MiClient.State.COMM:
                break
            await self.ble.wait_notify(secs=0.2)

        if self.get_state() != MiClient.State.COMM:
            raise TimeoutError("Pairing timeout")

        return self.token

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
            await self.ble.write(UUIDS.AVDTP, MiCommand.CMD_SEND_INFO)

        self.seq = ((MiClient.State.INIT, None),
                    (MiClient.State.SEND_KEY, on_send_key_state),
                    (MiClient.State.RECV_KEY, None),
                    (MiClient.State.RECV_INFO, on_recv_info_state),
                    (MiClient.State.SEND_DID, on_send_did_state),
                    (MiClient.State.CONFIRM, None),
                    (MiClient.State.COMM, None))
        self.seq_idx = 0
        await self.next_state()
        
        for _ in range(25):
            if self.get_state() == MiClient.State.COMM:
                break
            await self.ble.wait_notify(secs=0.2)
            
        if self.get_state() != MiClient.State.COMM:
            raise TimeoutError("Login handshake timeout")

    async def comm(self, cmd):
        if self.get_state() != MiClient.State.COMM:
            raise Exception("Not in COMM state. Retry maybe.")

        if isinstance(cmd, str):
            cmd = bytes.fromhex(cmd)

        self.received_data = b''
        
        if not self.keys:
            await self.ble.write_chunked(UUIDS.TX, cmd)
            for _ in range(10):
                await self.ble.wait_notify(secs=0.2)
                if self.received_data:
                    break
            return self.received_data if self.received_data else None

        res = MiCrypto.encrypt_uart(self.keys['app_key'], self.keys['app_iv'], cmd, it=self.uart_it)
        await self.ble.write_chunked(UUIDS.TX, res)
        self.uart_it += 1

        # OPRAVA 1: Počkáme minimálně na první 3 bajty, abychom zjistili očekávanou délku
        for _ in range(10):
            await self.ble.wait_notify(secs=0.1)
            if len(self.received_data) >= 3:
                break
                
        # OPRAVA 2: Pokud máme hlavičku, počkáme na zbytek paketu
        if len(self.received_data) >= 3:
            expected_size = self.received_data[2] + 5
            for _ in range(20):
                if len(self.received_data) >= expected_size:
                    break
                await self.ble.wait_notify(secs=0.1)

        if len(self.received_data) < 7:
            return None

        try:
            return MiCrypto.decrypt_uart(
                self.keys['dev_key'],
                self.keys['dev_iv'],
                self.received_data)[3:-4]
        except Exception as e:
            _LOGGER.debug("Decryption failed (InvalidTag or corrupted packet): %r", e)
            return None
from py_vapid import Vapid
import base64
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

v = Vapid()
v.generate_keys()

# Get base64url-encoded keys
priv_nums = v.private_key.private_numbers()
priv_bytes = priv_nums.private_value.to_bytes(32, byteorder='big')
priv_b64 = base64.urlsafe_b64encode(priv_bytes).decode().rstrip('=')

pub_bytes = v.private_key.public_key().public_bytes(Encoding.X962, PublicFormat.UncompressedPoint)
pub_b64 = base64.urlsafe_b64encode(pub_bytes).decode().rstrip('=')

print(f"VAPID_PRIVATE_KEY = \"{priv_b64}\"")
print(f"VAPID_PUBLIC_KEY = \"{pub_b64}\"")

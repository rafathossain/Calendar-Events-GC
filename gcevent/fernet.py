from cryptography.fernet import Fernet

# generate a key for encryption and decryption
# You can use fernet to generate
# the key or use random key generator
# here I'm using fernet to generate key
# key = Fernet.generate_key()
key = b'L4zn4W6hbc4BI1lvsMQsY_AAL2AlWIdIV4VhEvNF9qE='

# Instance the Fernet class with the key
fernet = Fernet(key)


def encryptMessage(message):
    # then use the Fernet class instance
    # to encrypt the string string must must
    # be encoded to byte string before encryption
    encMessage = fernet.encrypt(message.encode())
    return encMessage.decode('utf-8')


def decryptMessage(encMessage):
    # decrypt the encrypted string with the
    # Fernet instance of the key,
    # that was used for encrypting the string
    # encoded byte string is returned by decrypt method,
    # so decode it to string with decode methods
    encMessage = str(encMessage).encode()
    decMessage = fernet.decrypt(encMessage).decode()
    return decMessage

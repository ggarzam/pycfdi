import base64
import hashlib
from typing import Union
from pycfdi import exceptions
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding, utils
from cryptography.hazmat.primitives import serialization


def leer_certificado(cer_bytes: bytes) -> x509.Certificate:
    return x509.load_der_x509_certificate(cer_bytes)


def leer_llave_privada(key_bytes: bytes, password: str) -> rsa.RSAPrivateKey:
    try:
        return serialization.load_der_private_key(key_bytes, password=password.encode())
    except ValueError as e:
        if 'Incorrect password' in str(e):
            raise exceptions.crypto.IncorrectPasswordError()
        raise e


def sellar(message: Union[bytes, str], private_key: rsa.RSAPrivateKey) -> str:
    if isinstance(message, str):
        message = message.encode('utf-8')

    digest = hashlib.sha256(message).digest()

    signed = private_key.sign(
        digest,
        padding.PKCS1v15(),
        utils.Prehashed(hashes.SHA256())
    )

    return base64.b64encode(signed).decode('utf-8')


def certificado_base64(cer: x509.Certificate) -> str:
    encoding = serialization.Encoding.DER
    cer_bytes = cer.public_bytes(encoding)
    base64_bytes = base64.b64encode(cer_bytes)

    return base64_bytes.decode('utf-8')


def no_certificado(cer: x509.Certificate) -> str:
    hex_serial_number = '%x' % cer.serial_number
    serial_number_parts = [c for i, c in enumerate(hex_serial_number) if i % 2 != 0]

    return ''.join(serial_number_parts)


def is_pareja(cer: x509.Certificate, private_key: rsa.RSAPrivateKey) -> bool:
    encoding = serialization.Encoding.PEM
    fmt = serialization.PublicFormat.PKCS1

    return cer.public_key().public_bytes(encoding, fmt) == private_key.public_key().public_bytes(encoding, fmt)


def get_rfc(cer: x509.Certificate) -> str:
    return __get_subject_value_for_oid(
        cer=cer,
        oid=x509.NameOID.X500_UNIQUE_IDENTIFIER,
        attribute='RFC'
    )


def get_certificate_name(cer: x509.Certificate) -> str:
    return __get_subject_value_for_oid(
        cer=cer,
        oid=x509.NameOID.COMMON_NAME,
        attribute='Name'
    )


def __get_subject_value_for_oid(cer: x509.Certificate, oid: x509.ObjectIdentifier, attribute: str) -> str:
    attributes = cer.subject.get_attributes_for_oid(oid)

    if len(attributes) == 0:
        raise ValueError(f"Failed to read {attribute} from certificate.")

    return attributes[0].value.split('/')[0].strip()

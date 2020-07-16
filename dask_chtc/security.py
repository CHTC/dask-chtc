import shutil
import stat
from datetime import datetime, timedelta
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa

CERT_DIR = Path.home() / ".dask-chtc" / "certs"
CA_FILE = CERT_DIR / "ca.pem"
CERT_FILE = CERT_DIR / "cert.pem"

BACKEND = default_backend()

BASE_NAME_ATTRIBUTES = [
    x509.NameAttribute(x509.NameOID.COUNTRY_NAME, "US"),
    x509.NameAttribute(x509.NameOID.STATE_OR_PROVINCE_NAME, "WI"),
    x509.NameAttribute(x509.NameOID.LOCALITY_NAME, "Madison"),
    x509.NameAttribute(x509.NameOID.ORGANIZATION_NAME, "CHTC"),
]


def generate_private_key() -> rsa.RSAPrivateKeyWithSerialization:
    return rsa.generate_private_key(public_exponent=65537, key_size=2048, backend=BACKEND)


def generate_ca_and_key():
    now = datetime.utcnow()

    key = generate_private_key()

    subject = issuer = x509.Name(
        [*BASE_NAME_ATTRIBUTES, x509.NameAttribute(x509.NameOID.COMMON_NAME, "Dask-CHTC CA")]
    )
    ca = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(days=1))
        .not_valid_after(now + timedelta(days=365))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .sign(private_key=key, algorithm=hashes.SHA256(), backend=BACKEND)
    )

    return ca, key


def generate_server_cert_and_key(ca_cert, ca_key):
    """
    Generate a certificate for the

    Parameters
    ----------
    ca_cert
    ca_key
    common_name

    Returns
    -------

    """
    now = datetime.utcnow()

    key = generate_private_key()

    name = x509.Name(
        [*BASE_NAME_ATTRIBUTES, x509.NameAttribute(x509.NameOID.COMMON_NAME, "Dask-CHTC")]
    )

    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(ca_cert.subject)
        .not_valid_before(now - timedelta(days=1))
        .not_valid_after(now + timedelta(days=365))
        .serial_number(x509.random_serial_number())
        .public_key(key.public_key())
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                content_commitment=False,
                key_encipherment=True,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=False,
                crl_sign=False,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .add_extension(
            x509.ExtendedKeyUsage(
                [x509.ExtendedKeyUsageOID.CLIENT_AUTH, x509.ExtendedKeyUsageOID.SERVER_AUTH]
            ),
            critical=True,
        )
        .sign(private_key=ca_key, algorithm=hashes.SHA256(), backend=default_backend())
    )

    return cert, key


def save_cert_and_key(path: Path, cert: x509.Certificate, key: rsa.RSAPrivateKeyWithSerialization):
    path.parent.mkdir(exist_ok=True, parents=True)
    path.touch(mode=stat.S_IRUSR | stat.S_IWUSR, exist_ok=False)
    with path.open(mode="wb") as f:
        f.write(cert.public_bytes(encoding=serialization.Encoding.PEM))
        f.write(
            key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )

    return path


def _ensure_certs():
    # TODO: also check that the certs aren't expired/about to expire
    if CA_FILE.exists() and CERT_FILE.exists():
        return

    # Blow away any old certs lying around
    shutil.rmtree(CERT_DIR, ignore_errors=True)

    ca_cert, ca_key = generate_ca_and_key()
    cert, key = generate_server_cert_and_key(ca_cert, ca_key)

    save_cert_and_key(CA_FILE, ca_cert, ca_key)
    save_cert_and_key(CERT_FILE, cert, key)

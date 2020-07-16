import collections
import logging
import shutil
import stat
from datetime import datetime, timedelta
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

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


def generate_key() -> rsa.RSAPrivateKeyWithSerialization:
    """Generate an RSA private key."""
    return rsa.generate_private_key(public_exponent=65537, key_size=2048, backend=BACKEND)


CertAndKey = collections.namedtuple("CertAndKey", ("cert", "key"))


def generate_ca() -> CertAndKey:
    """
    Generate a new self-signed CA certificate.

    Returns
    -------
    ca_and_key : CertAndKey
        A :class:`CertAndKey` holding the newly-generated CA certificate and its
        private key.
    """
    now = datetime.utcnow()

    key = generate_key()

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

    return CertAndKey(ca, key)


def generate_cert(ca_and_key: CertAndKey) -> CertAndKey:
    """
    Generate a certificate signed by the given CA.

    Parameters
    ----------
    ca_and_key
        A :class:`CertAndKey` holding the CA certificate and corresponding key.

    Returns
    -------
    cert_and_key : CertAndKey
        A :class:`CertAndKey` holding the newly-generated certificate and its
        private key.
    """
    now = datetime.utcnow()

    key = generate_key()

    name = x509.Name(
        [*BASE_NAME_ATTRIBUTES, x509.NameAttribute(x509.NameOID.COMMON_NAME, "Dask-CHTC")]
    )

    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(ca_and_key.cert.subject)
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
        .sign(private_key=ca_and_key.key, algorithm=hashes.SHA256(), backend=default_backend())
    )

    return CertAndKey(cert, key)


def save_cert(path: Path, cert_and_key=CertAndKey) -> Path:
    """
    Save a :class:`CertAndKey` to a single file.
    The key and cert will be concatenated together.

    Parameters
    ----------
    path
        The path to save the file to.
    cert_and_key
        A :class:`CertAndKey` to save.

    Returns
    -------
    path : Path
        The path that they key and cert were saved to.
    """
    path = Path(path).absolute()
    path.parent.mkdir(exist_ok=True, parents=True)
    path.touch(mode=stat.S_IRUSR | stat.S_IWUSR, exist_ok=False)
    with path.open(mode="wb") as f:
        f.write(cert_and_key.cert.public_bytes(encoding=serialization.Encoding.PEM))
        f.write(
            cert_and_key.key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )

    return path


def delete_certs():
    """Remove **all** certificates managed by Dask-CHTC."""
    if not CERT_DIR.exists():
        return

    logger.debug("Deleting all existing Dask-CHTC certificates...")
    shutil.rmtree(CERT_DIR)
    logger.debug("Deleted all existing Dask-CHTC certificates.")


def ensure_certs():
    """
    Ensure that valid certificates that will continue to be valid for a while
    exist. If they don't exist, this function will create them. If they do exist,
    this function won't replace them.
    """
    if CA_FILE.exists() and CERT_FILE.exists():
        old_cert = x509.load_pem_x509_certificate(data=CA_FILE.read_bytes(), backend=BACKEND,)

        # check that the certs will not expire in the next two weeks
        if old_cert.not_valid_after > (datetime.utcnow() + timedelta(days=14)):
            logger.debug(
                "Skipping TLS certificate creation because we have existing long-lived certificates."
            )
            return

    logger.debug("Creating new TLS certificates...")

    # Blow away any old certs lying around
    delete_certs()

    ca = generate_ca()
    cert = generate_cert(ca)

    save_cert(CA_FILE, ca)
    save_cert(CERT_FILE, cert)

    logger.debug("Created new TLS certificates.")

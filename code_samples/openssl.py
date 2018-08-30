import cryptography.hazmat.backends as backends
import cryptography.hazmat.primitives.asymmetric.ec as ec
import cryptography.hazmat.primitives.hashes as hashes
import cryptography.hazmat.primitives.serialization as serialization
import cryptography.x509 as x509
	
	
class OpenSSL(object):
	
	def __get_ca_private_key(self):
	    if self.__root_ca_key_path is None:
	        raise Exception('You should have provided the ca\'s key')
	
	    ca_priv_key_file = open(self.__root_ca_key_path, 'rb')
	
	    ca_private_key = serialization.load_pem_private_key(
	        data=ca_priv_key_file.read(),
	        backend=backends.default_backend(),
	        password=None,
	        )
	
	    ca_priv_key_file.close()
	    return ca_private_key
	
	
	def _get_revoked(self, serial):
	    return x509.RevokedCertificateBuilder(
	        ).serial_number(
	            int(serial)
	        ).revocation_date(
	            datetime.datetime.today()
	        ).add_extension(
	            x509.CRLReason(x509.ReasonFlags.unspecified),
	            critical=False
	        ).build(backend=backends.default_backend())
	
	
	def _get_crl_builder(self, issuer_name, crl_number, last_update):
	    return x509.CertificateRevocationListBuilder(
	        ).issuer_name(
	            issuer_name
	        ).last_update(
	            last_update
	        ).next_update(
	            last_update + self.NEXT_UPDATE
	        ).add_extension(
	            x509.CRLNumber(crl_number),
	            critical=False
	        )    
	
	
	def create_empty_crl(self):
	    """
	    Generates a certification revocation list (CRL) with
	    a single revoked cert with serial = 1.
	
	    :rtype  str the path to the CRL.
	    """
	
	    cert = self.__get_ca_cert()
	    if self.__crl_path is None or self.__crl_path == '':
	        self.__crl_path = os.path.abspath(os.path.join(
	            self.__directory, 'crl.pem'))
	
	    crl_builder = self._get_crl_builder(
	        issuer_name=cert.issuer,
	        crl_number=1,
	        last_update=datetime.datetime.today()
	    )
	
	    revoked = self._get_revoked(1)
	    crl_builder = crl_builder.add_revoked_certificate(revoked)
	
	    crl = crl_builder.sign(
	        private_key=self.__get_ca_private_key(),
	        algorithm=hashes.SHA512(),
	        backend=backends.default_backend()
	    )
	
	    self.__write_public_bytes(self.__crl_path, crl)
	    return self.__crl_path
	
	def _basic_cert_setup(self, data, cert_type, serial=None):
	    """
	    Does a basic setup for the certificate.
	
	    -   deciding which curve to use
	    -   settings all of the attributes of the cert
	    -   generate a serial if it's not given
	
	    :rtype  tuple:
	    -   tuple[0]    private_key
	    -   tuple[1]    public_key
	    -   tuple[2]    str serial
	    -   tuple[3]    x509.CertificateBuilder the cert builder
	    -   tuple[4]    datetime.datetime   issuing date
	    -   tuple[4]    datetime.datetime   expiration date
	    """
	    common_name = data['CommonName']
	    days = data.get('Days', 365)
	    email = data['Email']
	    organization_name = data['OrganizationName']
	
	    self.__current_security_level =\
	    self.__get_current_security_level(cert_type)
	
	    curve, curve_str =\
	        self.__get_curve(self.__current_security_level)
	
	    self.__curve = curve_str
	
	    private_key, public_key = self.__gen_keys_pair(curve)
	
	    cert_attributes = x509.Name([
		    x509.NameAttribute(x509.oid.NameOID.COUNTRY_NAME, 'IT'),
		    x509.NameAttribute(x509.oid.NameOID.ORGANIZATION_NAME,
		        organization_name),
		    x509.NameAttribute(x509.oid.NameOID.COMMON_NAME,
		        common_name),
		    x509.NameAttribute(x509.oid.NameOID.EMAIL_ADDRESS,
		        email),
	    ])
	
	    if serial is None:
	        serial = gen_random_serial()
	
	    issuing_date = datetime.datetime.now(datetime.timezone.utc)
	    expiration_date = issuing_date + datetime.timedelta(days=days)
	
	    builder = x509.CertificateBuilder(
	        ).subject_name(
	            cert_attributes
	        ).not_valid_before(
	            issuing_date
	        ).not_valid_after(
	            expiration_date
	        ).public_key(
	            public_key
	        ).serial_number(
	            serial
	        )
	
	    return (private_key, public_key, serial, builder,
	            issuing_date, expiration_date)        
	
	def __gen_keys_pair(self, curve):
	    private_key = ec.generate_private_key(
	        curve=curve,
	        backend=backends.default_backend())
	    public_key = private_key.public_key()
	
	def create_keys_and_cert(self, data, cert_type, serial=None):
	    """
	    Does the following:
	    -   generates a key pair using ECDSA
	    -   generates a certificate for that public key
	    -   save to two files the certificate and the private key
	
	    :param  data    dict, keys:
	    -   `CommonName`   str the `CommonName` to insert into
	        the cert
	    -   `Email` str the `email` to insert into the cert
	    -   `Days`  int the days for which the cert is valid
	    starting from now
	    -   `OrganizationName`  str the `OrganizationName` to
	        insert into the cert
	    :param  cert_type   enum of `CertType`
	    :param  serial  str the optional serial to insert into the
	            certificate.
	    If `None`, a brand new one is generated using
	        randomness.
	
	    :note   `serial`, if is not `None`, should be pseudorandom.
	
	    :rtype  tuple, as follows:
	    -   tuple[0] = (path-to-cert, path-to-privkey-file)
	    -   tuple[1] = (serial, issuing date, expiration date)
	
	    :raises ValueError if `serial == 1`
	    """
	
	    if serial is not None and (serial == 1 or serial == '1'):
	        raise ValueError('serial cant be = 1')
	
	    truncated_name = utils.get_truncated_name(data['CommonName'])
	
	    self.__key_file_name = os.path.abspath(os.path.join(
	    self.__directory, truncated_name+'.key'))
	
	    self.__cert_file_name = os.path.abspath(os.path.join(
	    self.__directory, truncated_name+'.crt'))
	
	    result = self._basic_cert_setup(data, cert_type, serial)
	
	    private_key = result[0]
	    # public_key = result[1]
	    serial = result[2]
	    cert_builder = result[3]
	    issuing_date = result[4]
	    expiration_date = result[5]
	
	    extensions = None
	    if cert_type == CertType.server:
	        extensions = x509.ExtendedKeyUsage(
	            [x509.oid.ExtendedKeyUsageOID.SERVER_AUTH])
	    elif cert_type == CertType.client:
	        extensions = x509.ExtendedKeyUsage(
	            [x509.oid.ExtendedKeyUsageOID.CLIENT_AUTH])
	
	    cert_builder = cert_builder.add_extension(extensions,
	        critical=False)
	
	    ca_private_key = self.__get_ca_private_key()
	    ca_cert = self.__get_ca_cert()
	
	    cert_builder = cert_builder.issuer_name(
	    ca_cert.subject)
	
	    cert = cert_builder.sign(private_key=ca_private_key,
	        algorithm=hashes.SHA512(),
	        backend=backends.default_backend())
	
	    ca_private_key = None
	
	    private_key_output = open(self.__key_file_name, 'wb')
	    private_key_output.write(private_key.private_bytes(
	        encoding=serialization.Encoding.PEM,
	        format=serialization.PrivateFormat.TraditionalOpenSSL,
	        encryption_algorithm=serialization.NoEncryption()
	    ))
	    private_key_output.close()
	    private_key = None
	
	    self.__write_public_bytes(self.__cert_file_name, cert)
	
	    return (self.__cert_file_name,
	            self.__key_file_name), (serial,
	                                    issuing_date,
	                                    expiration_date)
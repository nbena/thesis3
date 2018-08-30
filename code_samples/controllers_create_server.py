@transaction.atomic
def create_server(input_data):
    """
    The function used to create a new server.

    :param  input_data: dict
    :rtype tuple: (directory-in-wich-files-will-be, work_id,
        server.id, server_conf)
    """

    is_key_valid = sshclient.is_key_valid(
        private_key=input_data['SSHPrivateKey'],
        is_from_file=False,
        private_key_passphrase=None,
        key_algo=input_data['SSHKeyAlgorithm']
    )

    if not is_key_valid:
        raise paramiko.ssh_exception.SSHException(WRONG_SSH_KEY)

    directory, work_id = misc_ops.create_temp_directory_work_id()

    chacha_supported = is_chacha_supported()

    try:
        server_vpn_net = ipaddress.IPv4Network(
            input_data['VPNVirtualNetID'] +
            '/'+input_data['VPNVirtualMask']
        )

        server = models.Server(
            public_host_name=input_data['publicHostName'],
            public_port=input_data['publicPort'],
            internal_ip=input_data['internalIP'],
            vpn_net=server_vpn_net,
            ssh_username=input_data['SSHUsername'],
            ssh_port=input_data['SSHPort'],
            ssh_private_key=input_data['SSHPrivateKey'],
            ssh_key_algorithm=input_data['SSHKeyAlgorithm']
        )

        create_server_in = {
            'ServerName': input_data['publicHostName'],
            'SupportChaCha': chacha_supported,
            'ServerPort': input_data['publicPort'],
            'VPNNet': {
                'NetID': input_data['VPNVirtualNetID'],
                'Mask': input_data['VPNVirtualMask'],
            }
        }

        # creating the main configuration file.
        server_conf = createserver.ServerConf(
            directory,
            create_server_in
        )

        # dict that contains the paths used by the server.
        server_dst_paths = server_conf.get_paths()

        server.private_key_path = server_dst_paths['key_path']
        server.public_key_path = server_dst_paths['cert_path']

        # effectively creates the file.
        server_conf.create_file()

        cert_res = cert_ops.generate_server_cert(
            directory,
            input_data['publicHostName'], email=input_data['email'])

        creation_info = cert_res[0]
        keys_info = cert_res[1]

        server_cert_paths = creation_info[0]

        serial = creation_info[1][0]
        issuing_date = creation_info[1][1]
        expiration_date = creation_info[1][2]

        security_level = keys_info[0]
        curve = keys_info[1]

        # certificate model
        cert = models.CertInfo(
            email=input_data['email'],
            security_level=security_level,
            algorithm=curve,
            certificate_serial=serial,
            issuing_date=issuing_date,
            expiration_date=expiration_date,
            common_name=input_data['publicHostName']
        )

        cert.save()

        server.base_per_client_dir_path = server_dst_paths[
            'base_ccd_path']
        server.client_up_script_file_path = server_dst_paths[
            'client_up_path']
        server.client_down_script_file_path = server_dst_paths[
            'client_down_path']

        server.crl_file_path = server_dst_paths['crl_path']

        server.vpn_nic = server_conf.get_device_name()

        server.certificate = cert
        server.save()

        work = misc_ops.get_create_server_work(
            directory=directory,
            server=server,
            server_cert_paths=server_cert_paths,
            server_conf=server_conf,
            server_dst_paths=server_dst_paths,
            transferCA=input_data['transferCA']
        )
        global ssh_worker
        misc_ops.add_host(ssh_worker, server)

        ssh_worker.put_work(work, work_id=work_id)
        return (directory, work_id, server.id, server_conf)

    except Exception as e:
        __shtuil_rmtree(directory)
        raise e
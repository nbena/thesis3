@transaction.atomic
def create_client(input_data):
    """
    Creates a new client.

    That means:
    -   creating config files
    -   creating a new pair of cryptographic keys
    -   registering a new mapping
    -   moving necessary to the server which this client is
        registered to.

    The configuration files are immediately returned as a
    zipped-then-base64ed file, you'll get a work id too, necessary
    to handle the moving of files to the server.
    """
    company = input_data['company']
    identifier = input_data['identifier']

    # first thing to do is to update dns
    dns_worker = dnsworker.DNSWorker()

    event_loop, requests = dns_worker.update_all_no_wait()

    full_name = utils.get_full_name(company, identifier)

    directory, _ = misc_ops.create_temp_directory_work_id()

    chacha_supported = is_chacha_supported()

    try:

        # getting the related server instance
        server = models.Server.objects.get(pk=input_data['idServer'])

        cert_res = cert_ops.generate_client_cert(
            directory, full_name,
            company, input_data['email'])

        creation_info = cert_res[0]
        keys_info = cert_res[1]

        serial = creation_info[1][0]
        issuing_date = creation_info[1][1]
        expiration_date = creation_info[1][2]

        # keys_info = client_openssl.keys_info
        security_level = keys_info[0]
        curve = keys_info[1]

        cert = models.CertInfo(
            email=input_data['email'],
            security_level=security_level,
            algorithm=curve,
            certificate_serial=serial,
            issuing_date=issuing_date,
            expiration_date=expiration_date,
            common_name=full_name,
        )

        cert.save()

        pair = creation_info[0]

        # creating the client model instance
        client = models.Client(
            # common_name=full_name,
            company=company,
            identifier=identifier,
            certificate=cert
        )

        client.save()

        pair = creation_info[0]

        create_client_in = {
            'SupportChaCha': chacha_supported,
            'ClientName': full_name,
            'ServerName': server.public_host_name,
            'ServerPort': server.public_port,
            'ServerCertName': server.certificate.common_name,
        }

        # copying the move-files.sh into the directory
        # in which we currently are.

        # this can be used on the client-side to move OpenVPN
        # files to the correct locations.
        move_script_file_name = os.path.join(directory, 'move-files.sh')

        shutil.copyfile(settings.MOVE_SCRIPT_FILE_CLIENT,
                        move_script_file_name)

        # we need the ca.crt too
        dest_ca = os.path.abspath(os.path.join(directory, 'ca.crt'))
        shutil.copyfile(settings.ROOT_CA_CERT, dest_ca)

        # getting the mapper instance.
        db = hdldb.HLDb()
        dnmcp = dnmcp4.DNMCP4(database_conn=db)

        nets_to_remap = input_data['internalNets']

        # now waiting the dns resolver
        dns_worker.wait_multi(event_loop, requests)

        mappings = dnmcp.create_mapping(
            server=server,
            client=client,
            old_nets=nets_to_remap)

        add_client_in = {
            'ServerVirtualIP': server.get_server_vpn_ip_address(),
            'ClientName': full_name,
            'InternalNets': [remapped.old_network for remapped in mappings],
            'ServerVirtualNICName': server.vpn_nic,
        }

        a_client = addclient.AddClient(
            directory,
            add_client_in
        )

        a_client.create_file()

        work = misc_ops.get_create_client_work(
            directory=directory,
            server=server,
            add_client=a_client,
            client_full_name=full_name
        )

        global ssh_worker
        ssh_worker.put_work(
            work_id=client.id,
            work=work
        )

        c_client = createclient.ClientConf(
            directory,
            create_client_in
        )

        c_client.create_file()

        # passing the mapping to the *Tables handler.
        xptables_remapping = mappings

        xtables_in = {
            'ClientName': full_name,
            'VPNNet': {
                'NetID': server.vpn_net.exploded,
                'Mask': server.vpn_net.netmask.exploded,
            },
            'InternalNets': input_data['internalNets'],
            'Remapping': xptables_remapping
        }

        client_xtables = nftables.NFTables(directory, xtables_in)

        client_xtables.create_file()

        zip_file = zipper.Zipper(
            directory=directory,
            zipfile_name=full_name+'.zip'
        )

        files_to_add = [
            client_xtables.file_name,
            c_client.file_name,
            pair[0],
            pair[1],
            dest_ca,
            move_script_file_name,

        ]

        for file_to_add in files_to_add:
            zip_file.add_file(file_to_add)

        zip_file.finalize()

        return (directory, zip_file.zip_abs_path, client.id)
    except Exception as e:
        __shtuil_rmtree(directory)
        raise e
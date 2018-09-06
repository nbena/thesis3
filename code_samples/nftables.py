import ipaddress
from io import StringIO

import cconf.dnmcp.ip_utils as ip_utils

from . import abstract_tables

COMMENT = """\t# map 'mapping' is applied in postrouting for 
\t# packets targt_net -> mooncloud_net, it changes the
\t# source addresses to the ones expected by mooncloud.

\t# map 'remapping' is applied in prerouting for
\t# packets mooncloud_net -> target_net, it changes the
\t# dest addresses from the mapped ones known by mooncloud
\t# to real ones.

\t# since OpenVPN server does NAT to the VPN, the only
\t# address known here is the VPN subnet."""


class NFTables(abstract_tables.AbstractTables):
    """
    Class that creates the mapping file for `nftables`.

    The `shebang` is set to `#!/usr/sbin/nft -f`.
    """

    def __init__(self, directory, data):
        super().__init__(directory, data, 'nftables.nft')

    def _mapping_str(self):
        nftables_initial = StringIO()
        nftables_mapping = StringIO()
        nftables_remapping = StringIO()
        nftables_masquerading = StringIO()

        final_rules = StringIO()

        nftables_initial.write('#!/usr/sbin/nft -f\n')
        nftables_initial.write('\n')

        nftables_initial.write('# creating the new table\n')
        nftables_initial.write('table ip ovpn_nat {\n')

        nftables_mapping.write('\t# map old -> new\n')
        nftables_mapping.write('\tmap mapping {\n')
        nftables_mapping.write('\t\ttype ipv4_addr: ipv4_addr\n')

        nftables_remapping.write('\t# map new -> old\n')
        nftables_remapping.write('\tmap remapping {\n')
        nftables_remapping.write('\t\ttype ipv4_addr: ipv4_addr\n')

        first = True

        # -j MASQUERADE on everything that comes from the VPN
        for address in self._internal_nets_cidr:
            rule = (
                '\t\tip saddr ' + self._vpn_net_cidr + ' ip daddr '
                + address + ' masquerade'
            )
            nftables_masquerading.write(rule+'\n')

        # building the two maps
        for mapping in self._mappings:

            old_net = mapping.old_network
            new_net = mapping.new_network
            count = mapping.counter
            starting_old_net_address = mapping.old_network_starting_address
            starting_new_net_address = mapping.new_network_starting_address

            if isinstance(old_net, str):
                old_net = ip_utils.CustomIPv4Network(old_net)

            if isinstance(new_net, str):
                new_net = ip_utils.CustomIPv4Network(new_net)

            if isinstance(starting_old_net_address, str):
                starting_old_net_address =\
                    ipaddress.IPv4Address(starting_old_net_address)

            if isinstance(starting_new_net_address, str):
                starting_new_net_address =\
                    ipaddress.IPv4Address(starting_new_net_address)

            ending_old_address = starting_old_net_address + count - 1
            current_old_address = starting_old_net_address
            current_remapped_address = starting_new_net_address
            i = 1

            mapping_element = ''
            remapping_element = ''
            while current_old_address <= ending_old_address:

                new_addr = current_remapped_address.exploded
                original_addr = current_old_address.exploded

                prefix = '\t\t\t\t'
                if first:
                    prefix = '\t\telements = {\t'
                    first = False

                if i % 2 == 0 and prefix != '\t\telements = {\t':
                    prefix = ' '

                end = ','
                if current_old_address == ending_old_address:
                    end = '}'

                current_remapping_element = (prefix + new_addr +
                                             ' : ' + original_addr+end)
                current_mapping_element = (
                    prefix + original_addr + ' : ' + new_addr+end)

                if i % 2 == 0:
                    # new line
                    mapping_element = (mapping_element +
                                       current_mapping_element + '\n')
                    remapping_element = (remapping_element +
                                         current_remapping_element + '\n')

                    nftables_mapping.write(mapping_element)
                    nftables_remapping.write(remapping_element)
                else:
                    # else stay on this line
                    mapping_element = current_mapping_element
                    remapping_element = current_remapping_element

                # shift to next elements
                mapping_element = current_mapping_element
                remapping_element = current_remapping_element

                current_remapped_address = current_remapped_address + 1
                current_old_address = current_old_address + 1

                i += 1

            nftables_mapping.write('\t}\n')
            nftables_remapping.write('\t}\n')

        final_rules.write(nftables_initial.getvalue()+'\n')

        final_rules.write(nftables_mapping.getvalue()+'\n')

        final_rules.write(nftables_remapping.getvalue()+'\n')

        # writing the comment
        final_rules.write(COMMENT+'\n\n')

        # declaring chains
        prerouting_chain = (
            '\tchain prerouting {\n' +
            '\t\ttype nat hook prerouting priority 0; policy accept;\n' +
            '\t\tip saddr ' + self._vpn_net_cidr + ' dnat to ip daddr map @remapping\n' +
            '\t}\n'
        )

        postrouting_chain = (
            '\tchain postrouting {\n' +
            '\t\ttype nat hook postrouting priority 0; policy accept;\n' +
            nftables_masquerading.getvalue() +
            '\t\tip daddr ' + self._vpn_net_cidr + ' snat to ip saddr map @mapping\n' +
            '\t}\n'
        )

        final_rules.write('\t# chains\n')
        final_rules.write(prerouting_chain)
        final_rules.write(postrouting_chain)

        # the last newline is important
        # nft will signal an error if it's not present.
        final_rules.write('}\n')

        return final_rules.getvalue()

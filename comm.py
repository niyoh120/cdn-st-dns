from typing import List
import ipaddress
import maxminddb


def get_cn_ip_range(geoip_cn_db_path) -> List[ipaddress.IPv4Network]:
    cn_ip_range_list = []
    with maxminddb.open_database(geoip_cn_db_path) as reader:
        for network, record in reader:
            if network.version == 4 and record["country"]["iso_code"] == "CN":
                cn_ip_range_list.append(network)
    return cn_ip_range_list


def exclude_address(
    net1: ipaddress.IPv4Network, net2: ipaddress.IPv4Network
) -> List[ipaddress.IPv4Network]:
    assert net1.version == net2.version

    # 如果net1在net2中，结果为空
    if net1.subnet_of(net2):
        return []
    # 如果net2在net1中，结果是net1中不在net2中的部分
    elif net2.subnet_of(net1):
        return list(net1.address_exclude(net2))
    # 如果net1和net2不相交，结果是net1
    elif not net1.overlaps(net2):
        return [net1]
    # 如果net1和net2有重叠，结果是net1不在重叠部分以外的部分
    else:
        overlap_start = max(net1.network_address, net2.network_address)
        overlap_end = min(net1.broadcast_address, net2.broadcast_address)
        overlap_list = list(
            ipaddress.summarize_address_range(overlap_start, overlap_end)
        )
        return [
            network
            for overlap in overlap_list
            for network in net1.address_exclude(overlap)
        ]

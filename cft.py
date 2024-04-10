from typing import List
import ipaddress

import httpx

import comm


# https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-regions-availability-zones.html#availability-zones-describe
def get_all_ip_range(
    allow_region: List[str],
    geoip_cn_path="./resources/Country-only-cn-private.mmdb",
) -> List[ipaddress.IPv4Network]:

    AWS_IP_RANGE_URL = "https://ip-ranges.amazonaws.com/ip-ranges.json"
    resp = httpx.get(AWS_IP_RANGE_URL)
    ip_range_data = resp.json()["prefixes"]
    result = []

    cn_ip_range_list = comm.get_cn_ip_range(geoip_cn_path)
    for ip_range_info in ip_range_data:
        service = ip_range_info.get("service")
        if service == "CLOUDFRONT":
            region = ip_range_info.get("region")
            if region in allow_region:
                ip_range = ipaddress.IPv4Network(ip_range_info["ip_prefix"])
                if region == "GLOBAL":
                    ip_range_list = [ip_range]
                    for cn_ip_range in cn_ip_range_list:
                        current_result = []
                        for ip_range in ip_range_list:
                            current_result.extend(
                                comm.exclude_address(ip_range, cn_ip_range)
                            )
                        ip_range_list = current_result
                    result.extend(current_result)
                else:
                    result.append(ip_range)
    return result

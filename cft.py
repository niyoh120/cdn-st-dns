from typing import List
import httpx


# https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-regions-availability-zones.html#availability-zones-describe
def get_all_ip_range(allow_region_list: List[str]) -> List[str]:
    AWS_IP_RANGE_URL = "https://ip-ranges.amazonaws.com/ip-ranges.json"
    resp = httpx.get(AWS_IP_RANGE_URL)
    ip_range_data = resp.json()["prefixes"]
    result = []
    for ip_range_info in ip_range_data:
        service = ip_range_info.get("service")
        if service == "CLOUDFRONT":
            region = ip_range_info.get("region")
            if region in allow_region_list:
                result.append(ip_range_info["ip_prefix"])
    return result


if __name__ == "__main__":
    for r in get_all_ip_range(
        [
            "ap-east-1",
            "ap-southeast-1",
            "ap-northeast-1",
            "ap-northeast-2",
            "GLOBAL",
        ]
    ):
        print(r)

import structlog
import CloudFlare
import ipaddress

logger = structlog.get_logger(__name__)


def get_dns_type(ip_str: str) -> str:
    ip = ipaddress.ip_address(ip_str)
    return "A" if ip.version == 4 else "AAAA"

def create_or_update_dns_record(
    token: str, domain: str, record_name: str, ip: str
) -> None:
    logger.info(f"更新{record_name}.{domain}的DNS记录为: {ip}")
    cf = CloudFlare.CloudFlare(token=token)

    # 获取域名的Zone ID
    zones = cf.zones.get(params={"name": domain})
    if len(zones) == 0:
        raise Exception("Domain not found in Cloudflare.")
    zone_id = zones[0]["id"]

    # 获取记录的Record ID
    record_exist = True
    records = cf.zones.dns_records.get(
        zone_id, params={"name": record_name + "." + domain, "type": get_dns_type(ip)}
    )
    if len(records) == 0:
        record_exist = False

    # 更新A记录的IP地址
    data = {
        "name": record_name + "." + domain,
        "type": "A",
        "content": ip,
        "proxied": False,
    }
    if record_exist:
        record_id = records[0]["id"]
        cf.zones.dns_records.put(zone_id, record_id, data=data)
    else:
        cf.zones.dns_records.post(zone_id, data=data)
    logger.info("更新DNS记录成功")

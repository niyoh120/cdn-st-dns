import tempfile
import os

import structlog
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
import httpx

import cf
import st
import cft


logger = structlog.get_logger(__name__)


def main():
    crontab = os.environ.get("CDN_ST_DNS_CRONTAB")

    def task():
        logger.info("开始执行任务")

        cst_path = os.environ["CDN_ST_DNS_CST_PATH"]
        geoip_cn_path = os.environ.get("CDN_ST_DNS_GEOIP_CN_PATH")
        geoip_cn_url = os.environ.get(
            "CDN_ST_DNS_GEOIP_CN_URL",
            "https://raw.githubusercontent.com/Loyalsoldier/geoip/release/Country-only-cn-private.mmdb",
        )
        cst_result_num = int(os.environ.get("CDN_ST_DNS_CST_RESULT_NUM", 5))
        cf_api_token = os.environ["CDN_ST_DNS_CF_API_TOKEN"]
        cf_domain = os.environ["CDN_ST_DNS_CF_DOMAIN"]
        cf_record = os.environ["CDN_ST_DNS_CF_RECORD"]
        cft_region_allowed = os.environ["CDN_ST_DNS_CFT_REGION_ALLOWED"]
        cft_domain = os.environ["CDN_ST_DNS_CFT_DOMAIN"]

        config_dict = {
            k: v for k, v in os.environ.items() if k.startswith("CDN_ST_DNS")
        }
        logger.info("获取配置完成\n" f"config_dict = {config_dict}")

        cft_region_allowed = cft_region_allowed.split(",")

        result_list = None
        with tempfile.TemporaryDirectory() as temp_dir:
            if geoip_cn_path is None:
                geoip_cn_path = os.path.join(temp_dir, "Country-cn.mmdb")
            if not os.path.exists(geoip_cn_path):
                logger.info("GEOIP数据库不存在, 开始下载")
                resp = httpx.get(geoip_cn_url)
                resp.raise_for_status()
                with open(geoip_cn_path, "wb") as f:
                    f.write(resp.content)
                logger.info("GEOIP数据库下载完成")

            ip_range_list = [
                str(ip_range)
                for ip_range in cft.get_all_ip_range(
                    allow_region=cft_region_allowed,
                    geoip_cn_path=geoip_cn_path,
                )
            ]
            if len(ip_range_list) < 1:
                logger.warn(f"{cft_region_allowed}, 这些区域中没有IP")
                return

            result_list = st.speed_test(
                cst_path=cst_path,
                work_dir=temp_dir,
                ip_range_list=ip_range_list,
                result_num=cst_result_num,
            )
            if len(result_list) < 1:
                logger.warn("没有找到合适的IP")
                return

        result_list = cft.filter_ip(result_list, cft_domain)

        if len(result_list) < 1:
            logger.warn(
                f"测速最快的{len(result_list)}个ip均不可用, 请增加候选数量后重新测试"
            )

            return

        logger.info(f"最合适的IP为: {result_list[0]}")

        cf.create_or_update_dns_record(
            token=cf_api_token,
            domain=cf_domain,
            record_name=cf_record,
            ip=result_list[0],
        )

        logger.info("执行成功")

    if crontab is not None:
        jobs = BlockingScheduler()
        jobs.add_job(task, CronTrigger.from_crontab(crontab))
        jobs.start()
    else:
        task()


if __name__ == "__main__":
    main()

import tempfile
import os

import structlog
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

import cf
import st
import cft


logger = structlog.get_logger(__name__)


def main():
    crontab = os.environ.get("CDN_ST_DNS_CRONTAB")

    def task():
        logger.info("开始执行任务")

        cst_path = os.environ["CDN_ST_DNS_CST_PATH"]
        cf_api_token = os.environ["CDN_ST_DNS_CF_API_TOKEN"]
        cf_domain = os.environ["CDN_ST_DNS_CF_DOMAIN"]
        cf_record = os.environ["CDN_ST_DNS_CF_RECORD"]
        cft_region_allowed = os.environ["CDN_ST_DNS_CFT_REGION_ALLOWED"]

        config_dict = {
            k: v for k, v in os.environ.items() if k.startswith("CDN_ST_DNS")
        }
        logger.info("获取配置完成\n" f"config_dict = {config_dict}")

        cft_region_allowed = cft_region_allowed.split(",")

        ip_range_list = cft.get_all_ip_range(cft_region_allowed)

        if len(ip_range_list) < 1:
            logger.warn(f"{cft_region_allowed}, 这些区域中没有IP")
            return

        result_list = None
        with tempfile.TemporaryDirectory() as temp_dir:
            result_list = st.speed_test(
                cst_path=cst_path,
                work_dir=temp_dir,
                ip_range_list=ip_range_list,
            )
            if len(result_list) < 1:
                logger.warn("没有找到合适的IP")
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
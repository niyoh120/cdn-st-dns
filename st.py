from typing import List
import csv
import os
import subprocess
import shutil

import structlog

logger = structlog.get_logger(__name__)


def speed_test(
    cst_path: str,
    work_dir: str,
    ip_range_list: List[str],
    st_url: str | None = None,
    result_num=1,
) -> list[str]:
    assert result_num > 0
    if not shutil.which(cst_path):
        raise Exception("测速工具路径不存在或不是可执行程序")

    ip_file = os.path.join(work_dir, "ip.txt")
    ip_range_list_str = "\n".join(ip_range_list)
    logger.info(f"更新IP列表至文件 {ip_file}")
    logger.info(f"IP列表:\n {ip_range_list_str}")
    with open(ip_file, "w") as f:
        f.write("\n".join(ip_range_list))

    # 执行CloudflareST，进行测速优选
    # ./CloudflareST -httping -f ip.txt -tl 150 -p 0 -url https://xxx.cloudfront.net/100m.test -o result.csv
    logger.info("进行IP优选")
    if st_url is None:
        cmd = [
            cst_path,
            "-f",
            "ip.txt",
            "-tl",
            "150",
            "-p",
            "0",
            "-dd",
            "-o",
            "result.csv",
        ]
    else:
        cmd = [
            cst_path,
            "-httping",
            "-f",
            "ip.txt",
            "-tl",
            "150",
            "-p",
            "0",
            "-url",
            st_url,
            "-o",
            "result.csv",
        ]
    subprocess.run(
        cmd,
        cwd=work_dir,
        check=True,
    )

    best_result_list = []
    # 没有可用ip时不会产生result.csv
    if not os.path.exists(os.path.join(work_dir, "result.csv")):
        return best_result_list
    with open(os.path.join(work_dir, "result.csv"), "r") as f:
        r = csv.reader(f)
        next(r)
        for _ in range(0, result_num):
            best_result_list.append(next(r)[0])
    return best_result_list

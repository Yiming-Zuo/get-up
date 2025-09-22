import argparse
import logging
import requests
import pendulum


from github import Github

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

GET_UP_ISSUE_NUMBER = 1
GET_UP_MESSAGE_TEMPLATE = (
    "今天的起床时间是--{get_up_time}.\r\n\r\n 起床啦，喝杯咖啡，背个单词，去跑步。\r\n\r\n 今天的一句诗:\r\n {sentence}"
)
SENTENCE_API = "https://v1.jinrishici.com/all"
DEFAULT_SENTENCE = "赏花归去马如飞\r\n去马如飞酒力微\r\n酒力微醒时已暮\r\n醒时已暮赏花归\r\n"
TIMEZONE = "Asia/Shanghai"


def login(token):
    return Github(token)


def get_one_sentence():
    """获取每日一句古诗词"""
    try:
        r = requests.get(SENTENCE_API, timeout=5)
        if r.ok:
            return r.json().get("content", DEFAULT_SENTENCE)
        else:
            logger.warning(f"诗句API请求失败，状态码: {r.status_code}")
            return DEFAULT_SENTENCE
    except (requests.RequestException, KeyError, ValueError) as e:
        logger.error(f"获取诗句失败: {e}")
        return DEFAULT_SENTENCE


def get_today_get_up_status(issue):
    """检查今天是否已经打卡"""
    comments = list(issue.get_comments())
    if not comments:
        return False
    latest_comment = comments[-1]
    now = pendulum.now(TIMEZONE)
    latest_day = pendulum.instance(latest_comment.created_at).in_timezone(TIMEZONE)
    # 修复日期比较逻辑，使用 date() 方法比较日期
    is_today = latest_day.date() == now.date()
    return is_today


def make_get_up_message():
    """生成起床打卡消息"""
    sentence = get_one_sentence()
    now = pendulum.now(TIMEZONE)
    # 4-10点算早起
    is_get_up_early = 4 <= now.hour <= 20
    get_up_time = now.to_datetime_string()
    body = GET_UP_MESSAGE_TEMPLATE.format(get_up_time=get_up_time, sentence=sentence)
    return body, is_get_up_early


def main(github_token, repo_name, weather_message):
    """主函数：执行起床打卡逻辑"""
    try:
        u = login(github_token)
        repo = u.get_repo(repo_name)
        issue = repo.get_issue(GET_UP_ISSUE_NUMBER)
        is_today = get_today_get_up_status(issue)

        if is_today:
            logger.info("今天已经记录过起床时间了")
            return

        early_message, is_get_up_early = make_get_up_message()
        body = early_message

        if weather_message:
            weather_message = f"现在的天气是{weather_message}\n"
            body = weather_message + early_message

        if is_get_up_early:
            issue.create_comment(body)
            logger.info("起床打卡成功，已创建GitHub评论")
        else:
            logger.warning("起床时间较晚，未记录打卡")
    except Exception as e:
        logger.error(f"程序执行出错: {e}")
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("github_token", help="github_token")
    parser.add_argument("repo_name", help="repo_name")
    parser.add_argument(
        "--weather_message", help="weather_message", nargs="?", default="", const=""
    )
    options = parser.parse_args()
    main(
        options.github_token,
        options.repo_name,
        options.weather_message,
    )

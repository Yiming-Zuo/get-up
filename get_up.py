import argparse
import requests
import pendulum


from github import Github

GET_UP_ISSUE_NUMBER = 1
GET_UP_MESSAGE_TEMPLATE = """🌅 早安打卡 | {date}
━━━━━━━━━━━━━━━━━━━━━━━━

⏰ 起床时间：{time}
{emoji} {evaluation}

📅 今天是今年的第 {day_of_year} 天
{progress_bar} {percentage:.1f}% ({day_of_year}/{total_days}){weather}

💪 起床啦，喝杯咖啡，背个单词，去跑步！

📖 今日诗句：
   {sentence}

━━━━━━━━━━━━━━━━━━━━━━━━
Keep going! 坚持就是胜利 ✨"""
SENTENCE_API = "https://v1.jinrishici.com/all"
DEFAULT_SENTENCE = "赏花归去马如飞\r\n去马如飞酒力微\r\n酒力微醒时已暮\r\n醒时已暮赏花归\r\n"
TIMEZONE = "Asia/Shanghai"


def login(token):
    return Github(token)


def get_year_progress(now):
    """计算年度进度"""
    day_of_year = now.day_of_year
    days_in_year = 366 if now.is_leap_year else 365
    percentage = (day_of_year / days_in_year) * 100
    return day_of_year, days_in_year, percentage


def make_progress_bar(percentage, length=20):
    """生成进度条"""
    filled = int(length * percentage / 100)
    bar = '█' * filled + '░' * (length - filled)
    return bar


def get_wake_up_emoji(hour):
    """根据起床时间返回对应的emoji和评价"""
    if 4 <= hour < 6:
        return "🌟", "超级早起！你是晨曦中的第一缕阳光"
    elif 6 <= hour < 8:
        return "☀️", "早起的鸟儿有虫吃"
    elif 8 <= hour < 10:
        return "🌤️", "美好的早晨"
    elif 10 <= hour < 12:
        return "⛅", "上午好"
    elif 12 <= hour <= 20:
        return "🌥️", "今天起得有点晚哦"
    else:
        return "🌙", "这个时间不算早起了"


def get_one_sentence():
    """获取每日一句古诗词"""
    try:
        r = requests.get(SENTENCE_API, timeout=5)
        if r.ok:
            return r.json().get("content", DEFAULT_SENTENCE)
        else:
            print(f"诗句API请求失败，状态码: {r.status_code}")
            return DEFAULT_SENTENCE
    except (requests.RequestException, KeyError, ValueError) as e:
        print(f"获取诗句失败: {e}")
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


def make_get_up_message(weather_message=""):
    """生成起床打卡消息"""
    sentence = get_one_sentence()
    now = pendulum.now(TIMEZONE)

    # 4-20点算早起
    is_get_up_early = 4 <= now.hour <= 20

    # 获取时间信息
    date = now.format('YYYY-MM-DD')
    time = now.format('HH:mm:ss')

    # 获取年度进度
    day_of_year, total_days, percentage = get_year_progress(now)

    # 生成进度条
    progress_bar = make_progress_bar(percentage)

    # 获取emoji和评价
    emoji, evaluation = get_wake_up_emoji(now.hour)

    # 处理天气信息
    weather = f"\n\n🌤️ 今日天气：{weather_message}" if weather_message else ""

    # 格式化消息
    body = GET_UP_MESSAGE_TEMPLATE.format(
        date=date,
        time=time,
        emoji=emoji,
        evaluation=evaluation,
        day_of_year=day_of_year,
        total_days=total_days,
        percentage=percentage,
        progress_bar=progress_bar,
        weather=weather,
        sentence=sentence
    )

    return body, is_get_up_early


def main(github_token, repo_name, weather_message):
    """主函数：执行起床打卡逻辑"""
    try:
        u = login(github_token)
        repo = u.get_repo(repo_name)
        issue = repo.get_issue(GET_UP_ISSUE_NUMBER)
        is_today = get_today_get_up_status(issue)

        if is_today:
            print("今天已经记录过起床时间了")
            return

        # 处理天气消息
        weather_info = weather_message.strip(": ") if weather_message else ""
        body, is_get_up_early = make_get_up_message(weather_info)

        if is_get_up_early:
            issue.create_comment(body)
            print("起床打卡成功，已创建GitHub评论")
        else:
            print("起床时间较晚，未记录打卡")
    except Exception as e:
        print(f"程序执行出错: {e}")
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

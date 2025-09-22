import argparse
import requests
import pendulum


from github import Github

GET_UP_ISSUE_NUMBER = 1
GET_UP_MESSAGE_TEMPLATE = """🌅 早安打卡 | {date}
━━━━━━━━━━━━━━━━━━━━━━━━

⏰ 起床时间：{time}
{emoji} {evaluation}

📅 今天是第 {day_of_year} / {total_days} 天  
{progress_bar} {percentage:.1f}% {weather}

💪 行文不辍，投稿不休！

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
    if 4 <= hour < 5:
        return "🌟", "超级早起！你是晨曦中的第一缕阳光"
    elif 5 <= hour < 6:
        return "☀️", "早起的鸟儿有虫吃"
    elif 6 <= hour < 8:
        return "🌤️", "美好的早晨"
    elif 8 <= hour < 9:
        return "⛅", "上午好"
    else:
        return "🌙", "这个时间不算早起了"


def calculate_consecutive_days(check_in_comments):
    """计算连续打卡天数"""
    if not check_in_comments:
        return 0

    # 按日期排序评论
    sorted_comments = sorted(check_in_comments,
                           key=lambda c: pendulum.instance(c.created_at).date())

    now = pendulum.now(TIMEZONE)
    today = now.date()
    consecutive = 0

    # 从最新的评论开始往前数
    for i in range(len(sorted_comments) - 1, -1, -1):
        comment_date = pendulum.instance(sorted_comments[i].created_at).in_timezone(TIMEZONE).date()
        expected_date = today - pendulum.duration(days=consecutive)

        if comment_date == expected_date:
            consecutive += 1
        else:
            break

    return consecutive


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


def analyze_get_up_records(issue):
    """分析所有打卡记录，生成统计数据"""
    comments = list(issue.get_comments())
    now = pendulum.now(TIMEZONE)

    # 过滤出打卡评论（排除统计评论）
    check_in_comments = []
    for comment in comments:
        if not comment.body.startswith("<!-- GET_UP_STATISTICS -->"):
            # 检查是否包含打卡标识
            if "早安打卡" in comment.body or "起床时间" in comment.body:
                check_in_comments.append(comment)

    # 统计数据
    total_days = len(check_in_comments)

    # 计算连续打卡天数
    consecutive_days = calculate_consecutive_days(check_in_comments)

    # 计算本月打卡情况
    current_month_count = 0
    current_month_early_count = 0
    for comment in check_in_comments:
        comment_date = pendulum.instance(comment.created_at).in_timezone(TIMEZONE)
        if comment_date.month == now.month and comment_date.year == now.year:
            current_month_count += 1
            # 检查是否早起（通过评论内容判断）
            if any(emoji in comment.body for emoji in ["🌟", "☀️", "🌤️"]):
                current_month_early_count += 1

    # 计算本年打卡情况
    current_year_count = sum(1 for c in check_in_comments
                            if pendulum.instance(c.created_at).in_timezone(TIMEZONE).year == now.year)

    return {
        'total_days': total_days,
        'consecutive_days': consecutive_days,
        'current_month_count': current_month_count,
        'current_month_early_count': current_month_early_count,
        'current_year_count': current_year_count,
        'last_check_in': check_in_comments[-1] if check_in_comments else None,
        'check_in_comments': check_in_comments
    }


def generate_month_calendar(stats):
    """生成本月打卡月历"""
    now = pendulum.now(TIMEZONE)

    # 获取本月的所有打卡记录
    current_month_checkins = {}
    for comment in stats['check_in_comments']:
        comment_date = pendulum.instance(comment.created_at).in_timezone(TIMEZONE)
        if comment_date.month == now.month and comment_date.year == now.year:
            day = comment_date.day
            # 判断是否早起
            is_early = any(emoji in comment.body for emoji in ["🌟", "☀️", "🌤️"])
            current_month_checkins[day] = "🌟" if is_early else "✅"

    # 获取本月第一天是星期几和总天数
    first_day = now.start_of('month')
    last_day = now.end_of('month')
    first_weekday = first_day.weekday()  # 0=Monday, 6=Sunday
    days_in_month = last_day.day

    # 生成月历
    calendar_lines = []
    calendar_lines.append(" 一  二  三  四  五  六  日")

    # 生成日历网格
    current_day = 1
    week = ["  "] * 7  # 初始化一周

    # 填充第一周的空白
    for i in range(first_weekday):
        week[i] = " · "

    # 填充日期
    for i in range(first_weekday, 7):
        if current_day <= days_in_month:
            if current_day in current_month_checkins:
                week[i] = f" {current_month_checkins[current_day]} "
            elif current_day <= now.day:
                week[i] = " ❌ "
            else:
                week[i] = " · "
            current_day += 1

    calendar_lines.append("".join(week))

    # 继续填充剩余的周
    while current_day <= days_in_month:
        week = ["  "] * 7
        for i in range(7):
            if current_day <= days_in_month:
                if current_day in current_month_checkins:
                    week[i] = f" {current_month_checkins[current_day]} "
                elif current_day <= now.day:
                    week[i] = " ❌ "
                else:
                    week[i] = " · "
                current_day += 1
            else:
                week[i] = " · "
        calendar_lines.append("".join(week))

    return "\n".join(calendar_lines)


def make_statistics_comment(stats):
    """生成统计评论内容"""
    now = pendulum.now(TIMEZONE)

    # 计算早起率
    early_rate = (stats['current_month_early_count'] / stats['current_month_count'] * 100
                 if stats['current_month_count'] > 0 else 0)

    # 生成月历视图
    calendar = generate_month_calendar(stats)

    template = """<!-- GET_UP_STATISTICS -->
# 📊 起床打卡统计

> 最后更新：{update_time}

## 📈 总览
- 🏆 总打卡天数：**{total_days}** 天
- 🔥 连续打卡：**{consecutive_days}** 天
- 📅 本年打卡：**{current_year_count}** 天

## 📅 {current_month}月统计
- 打卡天数：{current_month_count} 天
- 早起天数：{current_month_early_count} 天
- 早起率：{early_rate:.1f}%

## 🎯 打卡记录
```
{calendar}
```

**图例说明：**
- 🌟 早起打卡
- ✅ 普通打卡
- ❌ 未打卡
- · 未来日期

---
*统计数据每次打卡后自动更新*
"""

    return template.format(
        update_time=now.format('YYYY-MM-DD HH:mm:ss'),
        total_days=stats['total_days'],
        consecutive_days=stats['consecutive_days'],
        current_year_count=stats['current_year_count'],
        current_month=now.month,
        current_month_count=stats['current_month_count'],
        current_month_early_count=stats['current_month_early_count'],
        early_rate=early_rate,
        calendar=calendar
    )


def make_get_up_message(weather_message=""):
    """生成起床打卡消息"""
    sentence = get_one_sentence()
    now = pendulum.now(TIMEZONE)

    # 4-20点算早起
    is_get_up_early = 4 <= now.hour <= 10

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


def find_statistics_comment(issue):
    """查找统计评论"""
    comments = list(issue.get_comments())
    for comment in comments:
        if comment.body.startswith("<!-- GET_UP_STATISTICS -->"):
            return comment
    return None


def update_statistics(issue):
    """更新统计评论"""
    try:
        # 分析打卡记录
        stats = analyze_get_up_records(issue)

        # 查找现有的统计评论
        stats_comment = find_statistics_comment(issue)

        # 生成新的统计内容
        new_body = make_statistics_comment(stats)

        if stats_comment:
            # 更新现有评论
            stats_comment.edit(new_body)
            print("统计评论已更新")
        else:
            # 创建新的统计评论
            issue.create_comment(new_body)
            print("统计评论已创建")

    except Exception as e:
        print(f"更新统计失败: {e}")


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

            # 更新统计信息
            update_statistics(issue)
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

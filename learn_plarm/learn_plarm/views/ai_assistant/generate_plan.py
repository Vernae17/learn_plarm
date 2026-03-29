from flask import Blueprint, session, flash, jsonify, request

from learn_plarm.views.common import mysql_operate
from learn_plarm.views.common.call_deepseek import call_deepseek

aigp = Blueprint("generate_plan", __name__)

# 生成学习计划
@aigp.route("/api/generate_plan", methods = ["POST"])
def generate_plan():

    username = session['user']
    sql_user = 'SELECT id FROM learn_plarm.users WHERE username=%s'
    user_id0 = mysql_operate.db.select_db(sql_user,(username,))
    user_id = user_id0[0]['id']

    data = request.json
    goal = data.get('goal')
    days = data.get('days', 30)
    hours_per_day = data.get('hours', 1)

    if not goal:
        return jsonify({'error':'学习目标不能为空'}), 400

    prompt = f"""
        学习目标：{goal}
        计划时长：{days}天
        每天可投入时间：{hours_per_day}小时

        请生成一份详细的学习计划，包括：
        1. 阶段划分（基础期、提升期、冲刺期）
        2. 每日学习内容安排
        3. 学习资源推荐
        4. 阶段性检验标准
        """

    plan = call_deepseek(prompt, "你是一个专业的学业规划师")

    print(f"goal: {goal}, days: {days}, hours: {hours_per_day}")
    print(f"AI返回: {plan[:200] if plan else 'None'}")

    # 保存生成计划
    sql = 'INSERT INTO learn_plarm.learning_plans (user_id, goal, plan_content, days, hours_per_day) VALUES (%s, %s, %s, %s, %s)'
    mysql_operate.db.execute_db(sql,(user_id, goal, plan, days, hours_per_day))

    return jsonify({'success':True, 'plan':plan})
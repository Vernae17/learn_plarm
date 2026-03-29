from flask import Blueprint, session, redirect, render_template, url_for, flash, jsonify, request

from learn_plarm.views.common import mysql_operate
from learn_plarm.views.common.call_deepseek import call_deepseek

ais = Blueprint("summarize_note", __name__)

#智能笔记总结
@ais.route('/api/summarize_note',methods = ['GET', 'POST', 'PUT', 'DELETE'])
def summarize_note():
    """智能笔记总结"""
    username = session['user']

    sql_user = 'SELECT id FROM learn_plarm.users WHERE username = %s'
    user_id0 = mysql_operate.db.select_db(sql_user, (username,))
    user_id = user_id0[0]['id']

    #GET 获得所有 历史笔记总结
    if request.method == "GET":
        # 获取笔记ID参数
        note_id = request.args.get('id')

        # 如果指定了笔记ID，返回单个笔记详情
        if note_id:
            sql = """
            SELECT id, note_title, summary, created_at, original_content
            FROM learn_plarm.note_summaries
            WHERE id=%s AND user_id = %s
            """
            note = mysql_operate.db.select_db(sql,(note_id,user_id))
            return jsonify({"success":True, 'note':note[0]})

        # 否则，返回所有笔记详情
        sql_old_summary = """
            SELECT id, note_title, summary, created_at, original_content
            FROM learn_plarm.note_summaries
            WHERE user_id = %s 
            ORDER BY created_at DESC
            """
        notes = mysql_operate.db.select_db(sql_old_summary,(user_id,))
        # 转换数据
        #notes = convert_to_serializable(notes)

        print(f"/api/ai_recommend notes:{notes}")
        return jsonify({"success":True, 'notes':notes})

    #POST 创建新的笔记总结
    elif request.method == "POST":
        data = request.json
        note_title = data.get("title", "学习笔记")
        note_content = data.get("content")
        print(f"note_content:{note_content},note_title:{note_title}")

        if not note_content:
            return jsonify({'error': "笔记内容不能为空！"}),400

        summary = call_deepseek(f"请总结以下学习笔记，提炼核心要点：\n\n{note_content}")

        if not summary:
            return jsonify({"error": "生成总结失败！"})

        sql_summary = """
            INSERT INTO learn_plarm.note_summaries (user_id, note_title, original_content, summary, created_at)
            VALUES (%s, %s, %s, %s, NOW())
            """

        mysql_operate.db.execute_db(sql_summary, (user_id, note_title, note_content, summary))
        print(f"/api/ai_recommend summary:{summary}")

        return jsonify({'success': True, "summary": summary})

    elif request.method == "PUT":
        data = request.json
        note_id = data.get('id')  # 从请求中获取要更新的笔记ID
        note_title = data.get('title')
        note_content = data.get('content')

        if not note_id:
            return jsonify({'error': '笔记ID不能为空'}), 400

        # 更新笔记
        sql = """
            UPDATE learn_plarm.note_summaries 
            SET note_title=%s, original_content=%s 
            WHERE id=%s AND user_id=%s
        """
        mysql_operate.db.execute_db(sql, (note_title, note_content, note_id, user_id))

        # 重新生成总结
        if note_content:
            summary = call_deepseek(f"请总结以下学习笔记：\n\n{note_content}")
            if summary:
                sql_summary = 'UPDATE learn_plarm.note_summaries SET summary=%s WHERE id=%s AND user_id=%s'
                mysql_operate.db.execute_db(sql_summary, (summary, note_id, user_id))

        return jsonify({'success': True})

    # 删除笔记总结
    elif request.method == "DELETE":
        note_id = request.args.get('id')
        print({'note_id:':note_id})

        sql = """
            DELETE FROM learn_plarm.note_summaries WHERE id=%s AND user_id=%s
            """
        mysql_operate.db.execute_db(sql, (note_id, user_id))

        return jsonify({'success': True})

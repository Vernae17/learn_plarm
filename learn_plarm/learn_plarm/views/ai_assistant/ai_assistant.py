from flask import Blueprint, session, redirect, url_for, render_template

aiat = Blueprint("ai_assistant", __name__)

# 加一个ai助手功能
@aiat.route('/ai_assistant')
def ai_assistant():
    return render_template('ai_assistant.html')
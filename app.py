from flask import Flask, render_template, request, redirect, url_for, flash
from flask_socketio import SocketIO, join_room, leave_room, send

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Flash 메시지를 사용하기 위한 시크릿 키 설정
socketio = SocketIO(app)

# 임시로 팀 정보를 저장하는 딕셔너리 (키: 팀 ID, 값: 팀 정보)
team_data = {}

# 메인 페이지 - 팀 생성 또는 참가 선택 페이지
@app.route('/')
def home():
    return render_template('home.html')

# 팀 생성 페이지
@app.route('/create_team', methods=['GET', 'POST'])
def create_team():
    if request.method == 'POST':
        team_id = request.form['team_id']
        max_members = int(request.form['max_members'])
        student_id = request.form['student_id']

        if team_id in team_data:
            flash('이미 존재하는 팀 ID입니다. 다른 팀 ID를 선택해주세요.')
            return redirect(url_for('create_team'))

        # 팀 생성
        team_data[team_id] = {
            'members': [student_id],
            'max_members': max_members
        }

        flash(f'팀 {team_id}이(가) 생성되었습니다. 최대 인원은 {max_members}명입니다.')
        return redirect(url_for('chat', team_id=team_id))

    return render_template('create_team.html')

# 팀 참가 페이지
@app.route('/join_team', methods=['GET', 'POST'])
def join_team():
    if request.method == 'POST':
        team_id = request.form['team_id']
        student_id = request.form['student_id']

        if team_id not in team_data:
            flash('존재하지 않는 팀 ID입니다. 다시 시도해주세요.')
            return redirect(url_for('join_team'))

        team_info = team_data[team_id]

        # 최대 인원 확인
        if len(team_info['members']) >= team_info['max_members']:
            flash('해당 팀의 최대 인원이 이미 찼습니다. 다른 팀을 선택해주세요.')
            return redirect(url_for('join_team'))

        # 새로운 멤버 추가
        if student_id not in team_info['members']:
            team_info['members'].append(student_id)
        else:
            flash('이미 팀에 가입되어 있습니다.')

        return redirect(url_for('chat', team_id=team_id))

    return render_template('join_team.html')

# 팀 채팅방 페이지
@app.route('/chat/<team_id>')
def chat(team_id):
    if team_id not in team_data:
        return "Invalid team ID."

    team_info = team_data[team_id]
    return render_template('chat.html', team_id=team_id, max_members=team_info['max_members'], members=len(team_info['members']))

# 소켓 이벤트 - 팀 채팅방 참여
@socketio.on('join')
def on_join(data):
    team_id = data['team_id']
    student_id = data['student_id']
    join_room(team_id)
    send(f'{student_id} 님이 팀 {team_id} 채팅방에 입장했습니다.', to=team_id)

# 소켓 이벤트 - 메시지 보내기
@socketio.on('message')
def on_message(data):
    team_id = data['team_id']
    message = data['message']
    send(message, to=team_id)

if __name__ == '__main__':
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)

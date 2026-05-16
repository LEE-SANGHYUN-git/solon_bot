// =============================================
//  카카오톡 ↔ 서버 연동 메신저봇 R 스크립트
//  MessengerBot R (Android) 전용
// =============================================

// ── 설정 ─────────────────────────────────────
var CONFIG = {
  // 내 서버 주소 (HTTP)
  SERVER_URL: "http://192.168.0.233:8000/api/v1/summarize",

  // 봇이 응답할 방 이름 (빈 문자열이면 모든 방에서 동작)
  TARGET_ROOM: "",

  // 요청 타임아웃 (밀리초)
  TIMEOUT_MS: 10000,

  // 에러 메시지 (서버 연결 실패 시)
  ERROR_MSG: "⚠️ 서버에 연결할 수 없습니다. 잠시 후 다시 시도해주세요.",

  // 봇 자신이 보낸 메시지는 무시
  IGNORE_SELF: true,

  // 디버그 로그 출력 여부
  DEBUG: true,
};

// URL 감지 정규식
var URL_PATTERN = /https?:\/\/[^\s]+/;
// ─────────────────────────────────────────────

/**
 * 로그 출력 헬퍼
 */
function log(tag, msg) {
  if (CONFIG.DEBUG) {
    Log.d("[KakaoBot][" + tag + "] " + msg);
  }
}

/**
 * 서버로 메시지를 POST 요청으로 전송하고 응답 텍스트를 반환.
 * 실패 시 null 반환.
 *
 * Utils.http() 대신 org.jsoup 사용 (메신저봇 R 호환)
 *
 * 서버는 아래 JSON Body 를 수신합니다:
 * {
 *   "room"   : "채팅방 이름",
 *   "sender" : "보낸 사람 이름",
 *   "message": "메시지 내용",
 *   "isGroup": true | false
 * }
 *
 * 서버는 아래 형식으로 응답해야 합니다:
 * { "reply": "봇이 보낼 답장 텍스트" }
 * 또는 평문 텍스트(Content-Type: text/plain)도 허용합니다.
 */
function sendToServer(room, sender, message, isGroup) {
  try {
    var payload = JSON.stringify({
      room: room,
      sender: sender,
      message: message,
      isGroup: isGroup,
    });

    log("HTTP", "POST → " + CONFIG.SERVER_URL);
    log("HTTP", "Body  → " + payload);

    // org.jsoup 으로 HTTP POST 요청
    var response = org.jsoup.Jsoup.connect(CONFIG.SERVER_URL)
      .header("Content-Type", "application/json; charset=utf-8")
      .header("Accept", "application/json, text/plain, */*")
      .requestBody(payload)
      .ignoreContentType(true)
      .ignoreHttpErrors(true)
      .timeout(CONFIG.TIMEOUT_MS)
      .method(org.jsoup.Connection.Method.POST)
      .execute();

    var statusCode = response.statusCode();
    if (statusCode < 200 || statusCode >= 300) {
      log("HTTP", "비정상 응답 상태: " + statusCode);
      return null;
    }

    var body = response.body() ? response.body().trim() : "";
    log("HTTP", "응답 ← " + body);

    // JSON 응답 파싱 시도
    try {
      var json = JSON.parse(body);
      if (json && json.reply) {
        return json.reply;
      }
      // reply 키가 없으면 전체 JSON 문자열 그대로 반환
      return body;
    } catch (e) {
      // JSON 파싱 실패 → 평문 응답으로 처리
      return body || null;
    }
  } catch (e) {
    log("ERROR", "서버 요청 실패: " + e.message);
    return null;
  }
}

// =============================================
//  메신저봇 R 이벤트 핸들러
// =============================================

/**
 * 메시지 수신 이벤트
 * @param {string} room     - 채팅방 이름
 * @param {string} msg      - 수신된 메시지 내용
 * @param {string} sender   - 보낸 사람 이름
 * @param {boolean} isGroup - 단체 채팅방 여부
 * @param {object} replier  - 답장 객체 (replier.reply() 호출)
 * @param {boolean} isMention - 봇 멘션 여부
 */
function response(room, msg, sender, isGroup, replier, isMention) {
  // ── 방 필터링 ──────────────────────────────
  if (CONFIG.TARGET_ROOM && room !== CONFIG.TARGET_ROOM) {
    return; // 지정한 방이 아니면 무시
  }

  // ── 자기 자신 메시지 무시 ──────────────────
  if (CONFIG.IGNORE_SELF && sender === "나") {
    return;
  }

  log("MSG", "[" + room + "] " + sender + ": " + msg);

  // ── 명령어: !핑 (서버 연결 확인) ──────────
  if (msg.trim() === "!핑") {
    var pong = sendToServer(room, sender, "__ping__", isGroup);
    replier.reply(pong !== null ? "🟢 서버 연결 OK" : "🔴 서버 연결 실패");
    return;
  }

  // ── 명령어: !도움말 ────────────────────────
  if (msg.trim() === "!도움말") {
    replier.reply(
      "📖 사용 가능한 명령어\n" +
      "─────────────────\n" +
      "!핑     → 서버 연결 확인\n" +
      "!도움말 → 이 메시지 출력\n" +
      "그 외   → 서버로 전달 후 응답 출력"
    );
    return;
  }

  // ── URL이 없는 메시지는 무시 ──────────────
  if (!URL_PATTERN.test(msg)) {
    log("SKIP", "URL 없음 → 무시: " + msg);
    return;
  }

  // ── URL 포함 메시지: 서버로 전달 ──────────
  var reply = sendToServer(room, sender, msg, isGroup);

  if (reply === null || reply === "") {
    // 서버 응답 없음 또는 빈 응답 → 조용히 무시
    log("SKIP", "서버 응답 없음 또는 빈 응답 → 무시");
    return;
  }

  replier.reply(reply);
}

// ──────────────────────────────────────────────
//  봇 시작 이벤트 (선택)
// ──────────────────────────────────────────────
function onCreate(savedInstanceState, activity) {
  var textView = new android.widget.TextView(activity);
  textView.setText("카카오톡 ↔ 서버 봇이 시작되었습니다.");
  textView.setTextColor(android.graphics.Color.WHITE);
  activity.setContentView(textView);
}

function onStart(activity) { }
function onResume(activity) { }
function onPause(activity) { }
function onStop(activity) { }

# Elit d'Elitas

> 마인크래프트 서버 『무릉도원』을 모티브로 한, 돈버는 게임

## 할일

* 인벤토리 용량 늘리는 방법
* 밭 용량 늘리는 방법
* 채굴장
* 주문서

## `res/secret.json`

이 프로그램은 디스코드 토큰과 데이터베이스 접근 등, 
공개해서는 안 되는 코드를 필요로 합니다. 따라서 개발자는 아래 형식에 맞춰
`res/secret.json` 파일을 작성해야 합니다.

* `bot_token`: 디스코드 봇의 토큰입니다. 디스코드 봇 접근에 사용합니다.
* `database`
  * `user`: 데이터베이스 접근 사용자 아이디입니다.
  * `password`: 데이터베이스 접근 사용자 비밀번호입니다.
  * `host`: 데이터베이스의 위치입니다. 포트는 명시하지 않습니다.
  * `database_name`: 작업할 데이터베이스의 이름입니다. 기본값은 `elit`입니다.
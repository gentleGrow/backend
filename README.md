# 온라인 자산관리 프로젝트
![Ollass Logo](./etc/ollass.png)

## 프로젝트 개요

### 시작 배경

오프라인에서 엑셀을 활용한 자산관리를 하는 사용자가 많지만, 협업이 어렵고 공유가 제한적인 문제가 있었습니다. 이를 해결하기 위해 온라인에서 자산관리가 가능하며, 차트 및 데이터 분석 기능과 포트폴리오 공유 기능을 제공하는 웹사이트를 개발하였습니다.

### 개발 기간

- 2024년 3월 \~ 현재 진행 중

### 배포 사이트

- [www.ollass.com](http://www.ollass.com)


### 로컬 실행
> uvicorn main:app --host 0.0.0.0 --port 8000 --reload

### 팀 구성

- 백엔드 개발자 1명 (본인)
- 프론트엔드 개발자 1명
- 디자이너 1명

---

## 기술 스택

### 백엔드

- **FastAPI**: Python 기반 비동기 REST API 프레임워크
- **Docker**: 컨테이너화하여 배포 및 운영
- **AWS RDS MySQL (8.0.35, db.t3.micro)**: 관계형 데이터베이스
- **AWS Elasticache Redis (7.1.0, cache.t2.micro)**: 캐싱 및 세션 관리
- **AWS Elastic Beanstalk**: 로드 밸런서 및 오토스케일링을 지원하는 PaaS
- **AWS S3**: 정적 파일 저장
- **AWS Route53 & CloudFront**: 도메인 관리 및 CDN
- **Sentry**: 에러 로그 모니터링

---

## 시스템 아키텍처

### 인프라 구성

AWS 기반으로 구성된 아키텍처를 활용하며, 주요 요소는 다음과 같습니다.

- **EC2**: 데이터 수집 서버
- **Elastic Beanstalk**: 애플리케이션 서버 (ELB + Auto Scaling)
- **RDS MySQL**: 관계형 데이터 저장소
- **Elasticache Redis**: 세션 및 캐싱 서버
- **S3**: 정적 파일 저장소
- **Route53**: DNS 관리
- **CloudFront**: CDN 적용

> 비용 최소화를 위해 프로토타입 단계에서는 RDS 및 Elasticache를 Single Mode로 운영하며, 주기적인 스냅샷을 통해 데이터 백업을 진행합니다. 향후 유저 증가 시 Multi-AZ 배포 및 Read Replica를 통해 확장 예정입니다.

---

## 데이터 수집

### 데이터 소스

- **Yahoo Finance API**, **네이버 웹 스크래핑**
- 최소한의 비용으로 일별 주식 데이터를 수집하기 위해 두 가지 방식을 병행하였습니다.

### 데이터 수집 최적화

#### Yahoo Finance API

- 저렴한 비용으로 활용 가능하지만, 시간당 **Rate Limit 500**을 고려하여 일별 데이터만 수집
- API 호출이 웹 스크래핑보다 비용이 낮으므로, 공식 문서의 Rate Limit을 참조해 운영

#### 네이버 웹 스크래핑

- 국내 주식 데이터는 네이버 웹 스크래핑을 활용해 수집

### 실시간 데이터 수집 (임시 중단)

#### Polygon API (Legacy 보관 중)

- 초기 주식 데이터 수집은 **유료 Polygon API**를 활용하였으나, MVP 단계에서는 비용 절감을 위해 사용 중단

#### 네이버 실시간 데이터 웹 스크래핑 수집

- **멀티 프로세스로 분당 데이터 수집**을 진행
- CPU Credit 초과로 인해 추가 비용 발생 → 임시로 분당 데이터 수집 중단

### 데이터 수집 운영 방식

- **Celery 스케줄러**를 활용하여 단일 스크립트 파일로 데이터 수집 자동화
- 데이터 수집 오류 방지를 위해 **매일 검증 로직**을 실행하며, 미수집 발생 시 **이메일 알림** 기능 추가

---

## 데이터베이스 설계 및 최적화

### Redis 활용

- DB 부하 분산 및 connection 제한을 고려하여 세션 데이터 및 공통 데이터를 캐싱
- JWT Refresh Token 저장 및 유저 세션 관리
- 동일한 차트 데이터를 여러 요청에서 사용하는 경우 캐싱을 통해 94배 속도 개선 (22.8ms → 0.3ms)
- RPS 250 달성

### MySQL 최적화

- Read-heavy 서비스 특성을 고려하여 Multi-AZ 및 Read Replica 확장 계획
- Lazy evaluation을 활용하여 불필요한 쿼리 요청 제한
- N+1 문제 해결을 위해 `joinedload` 활용
- 실행 계획 분석 (`EXPLAIN`, `EXPLAIN ANALYZE`)을 통해 인덱스 활용 최적화
- 주식 종목별 최신 데이터를 가져오는 쿼리 개선

---

개발 방식

폴더 구조
```
.
├── Dockerfile
├── README.md
├── alembic/ (마이그레이션 관리)
├── app/ (주요 애플리케이션 코드)
│   ├── api/ (API 엔드포인트)
│   │   ├── asset/
│   │   ├── auth/
│   │   ├── chart/
│   │   ├── event/
│   │   └── v1/
│   ├── common/ (공통 유틸리티 및 미들웨어)
│   ├── data/ (데이터 관련 로직)
│   ├── module/ (비즈니스 로직)
│   └── main.py (애플리케이션 실행 파일)
├── database/ (데이터베이스 설정 및 초기화)
├── test/ (테스트 코드)
│   ├── unit/
│   ├── integration/
│   ├── performance/
│   └── fixtures/
├── etc/ (기타 설정 및 문서화)
└── docker-compose.yml
```
- 도메인 기반 디렉토리 구조를 채택하여 유지보수성을 높이고 역할을 분리
- API Router, Service, Validation 레이어로 구성하여 역할과 책임을 분리
- Dependency Injection (DI) 적용하여 결합도를 낮추고 유연한 구조 유지

### 코드 품질 관리

- `pre-commit hook`을 활용하여 코드 스타일 유지
  - `black`, `isort`, `flake8`, `mypy`, `pytest` 적용
- 브랜치 전략
  - `feature` → `dev` → `test` → `main`
  - feature 브랜치는 JIRA 티켓 번호와 매칭하여 관리

### 협업 방식

- **사용 툴**: JIRA, Confluence, Slack, Figma
- **애자일 스프린트 방식 적용**
  - 6주 단위 스프린트
  - 주요 개발 Task 및 유저 스토리 백로그 관리
  - `Definition of Done (DoD)` 문서화하여 팀원 간 일관된 목표 설정

---

## 테스트 및 성능 검증

### 통합 테스트 (Integration Test)

- `pytest`를 활용하여 API별 성공/실패 케이스 검증
- 모든 API별 2가지 테스트 케이스 적용 (성공/실패)

### 유닛 테스트 (Unit Test)

- 주요 비즈니스 로직을 `Given-When-Then` 방식으로 72개 테스트 케이스 작성
- 시간 부족으로 전체 커버리지는 확보하지 못했지만, MVP 안정화 후 보강 예정

### 부하 테스트 (Load Test)

- `Locust`를 활용하여 실제 유저 접속 상황을 시뮬레이션
- 유저당 11개 요청 기준, 최대 15명의 동시 접속을 허용하며 **RPS 250** 달성
- MySQL Connection Pool 제한을 고려하여 데이터 수집용 Connection을 별도 분리 (50개 + 10개)

---

## 로그인 및 보안

### JWT 기반 세션 관리

- **OAuth 로그인 지원**: Google, Naver, Kakao
- **JWT Access Token & Refresh Token 사용**
  - 짧은 Access Token과 긴 Refresh Token을 활용하여 보안 강화

### 로깅 및 모니터링

- **사용 툴**: `logger`, `Sentry`
- 서비스 장애 감지를 위한 실시간 모니터링 설정

---

## 프로젝트 비용 최적화

- 신입 개발자로 구성된 팀원의 부담을 줄이기 위해 **최소 비용으로 최대 효율**을 고려한 아키텍처 설계
- RDS 및 Redis는 **Single Mode**로 운영하며 필요 시 확장 가능하도록 구성
- 쿼리 최적화를 통해 DB 부하를 최소화하여 비용 절감

---

## 유저 피드백 반영

### 유저 인터뷰 및 설문조사

- 실 유저 4명 인터뷰, 30명 설문조사 진행
- 주요 개선 사항:
  - 매도 기능 추가
  - 정성적 데이터 추가 예정(메모 기능 등)

---

## 마무리

이 프로젝트는 온라인 자산관리의 새로운 대안을 제시하기 위해 시작되었습니다. 현재 프로토타입 단계이며, 앞으로 사용자 피드백을 반영한 기능 개선과 서비스 안정화 작업을 진행할 예정입니다.

더 나은 서비스를 위해 지속적으로 발전시켜 나가겠습니다!


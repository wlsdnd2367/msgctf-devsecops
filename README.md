MSGCTF DevSecOps CI/CD 계획서
1. 역할 및 목표
DevSecOps 역할
DevSecOps는 출제자가 제출한 문제 이미지를 다음 상태로 만드는 것을 목표로 한다.
* 안전한(Secure) 이미지
* 추적 가능한(Traceable) 이미지
* 재현 가능한(Repeatable) 이미지
* Runtime이 즉시 사용할 수 있는(Deployable) 이미지
즉, 단순히 Docker 이미지를 만드는 것이 아니라 다음 질문에 답할 수 있어야 한다.
반드시 추적 가능해야 하는 정보
* 어떤 Challenge가 생성한 이미지인가?
* 어떤 Commit 또는 제출 이미지에서 생성되었는가?
* Runtime이 사용해야 하는 Registry URL은 무엇인가?
* Runtime이 사용해야 하는 Digest는 무엇인가?
* Secret Scan은 통과했는가?
* Vulnerability Scan은 통과했는가?
* 배포 가능한 상태인가?
* 누가 승인했는가?

2. DevSecOps 원칙
MSGCTF는 제출된 이미지를 직접 신뢰하지 않는다.
신뢰하는 것은 다음뿐이다.
1. 검증된 Pipeline
2. 승인된 Image Digest
3. 생성된 Deployment Artifact
즉,
Challenge Input
↓
Validation
↓
Security Scan
↓
Approved Image
↓
Digest
↓
Artifact
↓
Runtime Deployment
구조를 따른다.

3. Challenge Intake 방식
MSGCTF는 두 가지 입력 방식을 지원한다.

Mode A : Source Build Pipeline
출제자가 소스코드를 저장소에 업로드하는 방식
흐름
Challenge Repo Push
↓
Metadata Validation
↓
Docker Build
↓
Gitleaks
↓
Trivy
↓
Registry Push
↓
Digest Extraction
↓
Artifact Generation
장점
* 완전한 재현 가능성
* 표준화된 저장소 구조
* Build 과정 추적 가능
단점
* 언어별 Build 환경 관리 필요
* 유지보수 비용 증가

Mode B : Submitted Image Pipeline
출제자가 Docker 이미지를 제출하는 방식
흐름
Challenge Metadata Push
↓
Metadata Validation
↓
Docker Pull
↓
Gitleaks
↓
Trivy
↓
Health Check
↓
Promotion to GHCR
↓
Digest Extraction
↓
Artifact Generation
장점
* 언어와 프레임워크에 독립적
* Python, Go, Node.js, PHP, Java 모두 지원
* DevSecOps 부담 감소
단점
* 이미지 내부 Build 과정은 추적 불가

MVP 결정
현재 MVP는
Mode B
를 기본 채택한다.
Mode A는 향후 확장 옵션으로 문서화한다.

4. Challenge Deployment Pipeline
담당
DevSecOps

Stage 1 : Metadata Validation
필수 파일
challenge.toml
필수 필드
challenge.id
challenge.category
deployment.resource_profile
deployment.container_port
monitoring.health_path
검증 실패 시 즉시 중단

Stage 2 : Secret Scan
도구
* Gitleaks
검사 대상
* GitHub Token
* GCP Credential
* AWS Credential
* Password
* API Key
* Private Key
정책
Secret 발견
→ 즉시 Fail

Stage 3 : Vulnerability Scan
도구
* Trivy
정책
Severity	정책
Critical	Fail
High	운영팀 검토
Medium	Report
Low	Report
MVP 기준
Critical 발견
→ 배포 차단

Stage 4 : Image Validation
실제 컨테이너 실행
검사
* 컨테이너 기동 여부
* 포트 바인딩
* Health Check
예시
GET /health
성공 조건
HTTP 200

Stage 5 : Promotion
승인된 이미지를
GHCR
로 승격
예시
ghcr.io/msgctf/web100

Stage 6 : Digest Extraction
예시
sha256:abcd1234...
Runtime은 Digest만 사용한다.

Stage 7 : Artifact Generation
예시
{
  "schema_version": "1.0",
  "challenge_id": "web100",
  "submitted_image": "ghcr.io/author/web100:v1",
  "image": "ghcr.io/msgctf/web100",
  "digest": "sha256:abcd...",
  "image_ref": "ghcr.io/msgctf/web100@sha256:abcd...",
  "scan_result": "PASS",
  "resource_profile": "small",
  "container_port": 5000,
  "health_path": "/health"
}

5. Registry 정책
Registry
GHCR 사용
이미지 태그
ghcr.io/msgctf/<challenge_id>:<commit_sha>
Runtime용
ghcr.io/msgctf/<challenge_id>@sha256:<digest>

규칙
허용
Digest 기반 참조
금지
latest 태그 기반 운영
latest는 사람이 보기 위한 용도로만 사용한다.

6. Secret Management
원칙
금지
* Docker Build Args에 Secret 전달
* Docker Layer 내 Secret 저장
* CI 로그 출력
* Repository 저장

권장 방식
Kubernetes Secret
또는
Secret Manager
예시
* GCP Secret Manager
* HashiCorp Vault

운영 전 점검
대회 시작 전
* Registry Token 교체
* Cloud Credential 교체
* 불필요한 Secret 제거

7. Build Metadata 관리
모든 Artifact는 다음 정보를 포함해야 한다.
challenge_id
source_repository
submitted_image
commit_hash
build_time
registry_url
digest
scan_result
resource_profile
container_port
health_path
목적
추적성 확보
감사 로그 확보
사후 분석 지원

8. Runtime Contract
Runtime 입력
{
  "challenge_id": "web100",
  "image_ref": "ghcr.io/msgctf/web100@sha256:abcd...",
  "digest": "sha256:abcd...",
  "resource_profile": "small",
  "container_port": 5000,
  "health_path": "/health",
  "scan_result": "PASS"
}
Runtime은 태그를 사용하지 않는다.

9. Scheduler Contract
Scheduler는 Resource Profile을 Kubernetes Resource로 변환한다.
예시
{
  "small": {
    "requests": {
      "cpu": "250m",
      "memory": "256Mi"
    },
    "limits": {
      "cpu": "500m",
      "memory": "512Mi"
    }
  }
}

10. Kubernetes 보안 정책
모든 Challenge Pod는 기본적으로
runAsNonRoot: true
readOnlyRootFilesystem: true
allowPrivilegeEscalation: false
설정 적용
추가 정책
* Privileged Container 금지
* HostPath Mount 금지
* Host Network 사용 금지
* 기본 Namespace 격리
* NetworkPolicy 적용
목적
문제 간 영향 최소화
클러스터 보호

11. 모니터링
알림 대상
Registry
* Push 실패
* Pull 실패
Runtime
* Health Check 실패
* Pod CrashLoopBackOff
Cluster
* CPU 과다 사용
* Memory 과다 사용

12. 롤백 정책
배포 후 문제 발생 시
Runtime은 이전 Digest로 롤백 가능해야 한다.
예시
Digest A
↓
Digest B 배포
↓
문제 발생
↓
Digest A 복구
태그 기반 롤백은 금지

13. 대회 당일 운영 절차
Image Freeze
대회 시작 전
모든 Challenge Image 승인 완료
Digest 확정
Artifact 확정
대회 중에는 원칙적으로 신규 이미지 배포 금지

예외 배포
필요 시
1. 운영팀 승인
2. 재스캔
3. 신규 Digest 생성
4. Artifact 재생성
과정을 거쳐야 한다.

14. 팀 간 협업 규격
Runtime Team
합의 사항
* Digest 기반 배포
* Pull Secret 사용 방식
* Namespace 정책
Backend Team
합의 사항
* challenge_id 형식
* Metadata Schema
Monitoring Team
합의 사항
* Alert 기준
* Health Check 방식
Security Team
합의 사항
* Trivy 기준
* 예외 승인 절차
* Secret 정책

15. MVP 완료 기준
다음 조건을 만족하면 DevSecOps MVP 완료로 본다.
* 샘플 Challenge 제출 가능
* Metadata 검증 가능
* Docker Image Pull 가능
* Gitleaks Scan 가능
* Trivy Scan 가능
* GHCR Push 가능
* Digest 추출 가능
* artifact.json 생성 가능
* Runtime이 Digest 기반으로 배포 가능
* Scheduler가 Resource Profile 적용 가능
즉,
Challenge
↓
Validation
↓
Scan
↓
GHCR
↓
Digest
↓
Artifact
↓
Runtime
↓
Scheduler
↓
GKE


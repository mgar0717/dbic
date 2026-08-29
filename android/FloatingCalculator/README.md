# 플로팅 계산기 (Floating Calculator)

화면 위에 떠서 다른 앱을 쓰면서도 바로 계산할 수 있는 안드로이드 계산기 앱입니다.
드래그로 위치 이동, 투명도(20~100%) 조절, 접기/펼치기 기능을 지원합니다.

## 빌드하기

Android Studio에서 이 폴더(`android/FloatingCalculator`)를 **Open**으로 열면
Gradle 동기화 후 바로 실행/빌드할 수 있습니다.

커맨드라인으로 APK만 만들려면:

```bash
cd android/FloatingCalculator
./gradlew assembleRelease
# 결과물: app/build/outputs/apk/release/app-release-unsigned.apk
```

배포용 서명 APK가 필요하면 `app/build.gradle.kts`에 `signingConfigs`를 추가하거나,
Android Studio의 **Build > Generate Signed App Bundle / APK** 메뉴를 사용하세요.

## 설치 후 사용법

1. 앱 실행 → **플로팅 계산기 시작** 버튼 클릭
2. "다른 앱 위에 표시" 권한 화면이 뜨면 이 앱에 대해 권한 허용
3. 화면 위에 반투명 계산기가 나타남
   - 상단 바(⋮⋮ 아이콘 쪽)를 드래그하면 위치 이동
   - 물방울 아이콘: 투명도 슬라이더 표시/숨김
   - ⌃/⌄ 아이콘: 계산기 접기/펼치기 (헤더만 남기고 숨기기)
   - ✕ 아이콘: 계산기 종료
   - 알림 영역에서도 "끄기"로 언제든 종료 가능

위치·투명도·접힘 상태는 기기에 저장되어 다음 실행 시 그대로 복원됩니다.

## 앱 용량을 최소화하기 위해 한 선택들

- **외부 라이브러리 없음**: AndroidX/AppCompat/Material 등 어떤 의존성도 추가하지 않고
  순정 프레임워크 API(`android.app.*`, `android.view.*`, `android.widget.*`)만 사용했습니다.
  (`app/build.gradle.kts`에 `dependencies` 블록이 아예 없습니다.)
- **minSdk 26**: Android 8.0(Oreo)부터 지원되는 `TYPE_APPLICATION_OVERLAY`를 기준으로 잡아
  구버전 호환 분기 코드를 없앴습니다.
- **아이콘은 전부 벡터(XML)**: 런처 아이콘(Adaptive Icon)과 알림 아이콘, 헤더 버튼 아이콘까지
  모두 `VectorDrawable`로만 구성해 해상도별 PNG를 두지 않았습니다.
- **R8 축소 활성화**: `release` 빌드에서 `isMinifyEnabled`, `isShrinkResources`를 켜서
  사용하지 않는 코드/리소스를 제거합니다.
- **단일 언어 리소스**: `resourceConfigurations`를 `ko`로 제한해 번역 리소스를 배제했습니다.
- **ViewBinding/DataBinding 미사용**: `findViewById`만 사용해 생성 코드/런타임 오버헤드를 줄였습니다.

## 필요한 권한

- `SYSTEM_ALERT_WINDOW` — 다른 앱 위에 계산기를 띄우기 위함
- `FOREGROUND_SERVICE`, `FOREGROUND_SERVICE_SPECIAL_USE` — 플로팅 창이 시스템에 의해
  강제 종료되지 않도록 포그라운드 서비스 + 알림으로 유지
- `POST_NOTIFICATIONS` — Android 13+ 에서 포그라운드 서비스 알림 표시용

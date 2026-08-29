plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "com.mgar.floatcalc"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.mgar.floatcalc"
        minSdk = 26
        targetSdk = 35
        versionCode = 1
        versionName = "1.0"

        // 앱 아이콘/문구만 있는 단일 언어 앱이라 다국어 리소스를 빼서 용량을 더 줄인다.
        resourceConfigurations += listOf("ko")
    }

    buildTypes {
        release {
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }

    buildFeatures {
        viewBinding = false
        buildConfig = false
    }
}

// 별도 외부 라이브러리 없이 Kotlin 표준 라이브러리 + 안드로이드 프레임워크 API만 사용해
// 설치 용량을 최소화한다 (AndroidX/AppCompat/Material 미사용).

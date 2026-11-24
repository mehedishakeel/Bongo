# APK Release Signing Guide

Bongo's CI pipeline automatically signs the Android APK on every tag-triggered release.
This document explains how to generate a keystore and wire it up as GitHub Actions secrets.

---

## 1 — Generate a Keystore (one-time)

> Do this **once** on your local machine. Keep the `.jks` file and all passwords in a password manager. **Never commit it to the repo.**

```bash
keytool -genkeypair \
  -v \
  -keystore bongo-release.jks \
  -keyalg RSA \
  -keysize 4096 \
  -validity 10000 \
  -alias bongo \
  -dname "CN=Bongo IME, OU=Engineering, O=Bongo, L=Dhaka, ST=Dhaka, C=BD"
```

You will be prompted for:
- **Keystore password** → save as `KEY_STORE_PASSWORD`
- **Key password** → save as `KEY_PASSWORD`
- The alias used (`bongo`) → save as `KEY_ALIAS`

---

## 2 — Base64-encode the Keystore

```bash
base64 -i bongo-release.jks | tr -d '\n' > bongo-release.jks.b64
```

Copy the contents of `bongo-release.jks.b64` — that's the value for `KEYSTORE_BASE64`.

---

## 3 — Add GitHub Actions Secrets

Go to **Settings → Secrets and variables → Actions → New repository secret** and add:

| Secret name | Value |
|---|---|
| `KEYSTORE_BASE64` | base64-encoded `.jks` contents (from step 2) |
| `KEY_STORE_PASSWORD` | Keystore password |
| `KEY_ALIAS` | `bongo` (or whatever alias you used) |
| `KEY_PASSWORD` | Key password |

---

## 4 — How CI Uses the Secrets

In `.github/workflows/release.yml`, the `build-android` job:

1. **Decodes** `KEYSTORE_BASE64` → `/tmp/bongo-release.jks`
2. **Passes** `BONGO_KEYSTORE_PATH`, `BONGO_KEY_STORE_PASSWORD`, `BONGO_KEY_ALIAS`, `BONGO_KEY_PASSWORD` as environment variables to Gradle
3. **Runs** `./gradlew assembleRelease` — Gradle picks up the env vars in `build.gradle.kts` and uses the `release` signingConfig
4. **Deletes** `/tmp/bongo-release.jks` in an `always()` cleanup step

**On forks / PRs:** The secrets won't be present, so the keystore decode step is skipped and Gradle silently falls back to the debug signing config — forks can still build and test locally.

---

## 5 — Verify the Signed APK (locally)

```bash
# Install apksigner (part of Android SDK build-tools)
apksigner verify --verbose Bongo-1.2.1-android.apk

# Or with jarsigner:
jarsigner -verify -verbose -certs Bongo-1.2.1-android.apk
```

A correctly signed APK will show:
```
Verified using v2 scheme (APK Signature Scheme v2): true
Verified using v3 scheme (APK Signature Scheme v3): true
```

---

## Notes

- The keystore uses **RSA-4096 / 10 000-day validity** — well beyond any foreseeable release window.
- The signing config in `build.gradle.kts` is **environment-variable-driven** — no plaintext passwords are ever stored in the repo.
- V1 (JAR), V2, V3, and V4 signing schemes are all enabled for maximum compatibility from Android 7 through Android 14+.

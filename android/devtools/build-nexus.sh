#!/bin/bash
# build-nexus.sh - compile release APK, notify and optionally send to Telegram
# place this file anywhere (e.g. /usr/local/bin/build-nexus) and make executable

# project location (adjust if your path differs)
PROJECT_DIR="$HOME/Downloads/DraftNexus-AI/android"
cd "$PROJECT_DIR" || exit

echo "🚀 Starting build in $PROJECT_DIR..."
export JAVA_HOME="/Library/Java/JavaVirtualMachines/microsoft-25.jdk/Contents/Home"

# destination file in Downloads; overwrite previous APK each run
DEST_FILE="$HOME/Downloads/DraftNexus-AI-release.apk"

# Telegram configuration (leave blank if you don't want to send)
TOKEN=""
CHAT_ID=""

if ./gradlew clean assembleRelease; then
    {
      cp app/build/outputs/apk/release/app-release.apk "$DEST_FILE" 2>/dev/null || \
      cp app/build/outputs/apk/release/app-release-unsigned.apk "$DEST_FILE" 
    }

    # notify locally
    osascript -e 'display notification "Build Berhasil! APK siap di Downloads" with title "DraftNexus-AI"'
    afplay /System/Library/Sounds/Glass.aiff
    echo "✅ APK ready in Downloads (Size: $(du -h \"$DEST_FILE\" | cut -f1))"
    open ~/Downloads

    # send via Telegram if configured
    if [[ -n "$TOKEN" && -n "$CHAT_ID" ]]; then
        echo "📤 Sending APK to Telegram..."
        curl -s -F document=@"$DEST_FILE" \
             -F caption="✅ Build Berhasil! ($TIMESTAMP)" \
             "https://api.telegram.org/bot$TOKEN/sendDocument?chat_id=$CHAT_ID" >/dev/null
    fi
else
    osascript -e 'display notification "Build GAGAL! Silakan cek terminal." with title "DraftNexus-AI"'
    afplay /System/Library/Sounds/Basso.aiff
    echo "❌ Build failed, see terminal output."
    exit 1
fi

echo "✨ Done!"

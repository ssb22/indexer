#!/bin/bash

export APP_WORKSPACE=/path/to/your/app/workspace
export ANDROID_HOME=/usr/local/adt-bundle-mac-x86_64-20140702/sdk # or whatever
export KEYSTORE_USER=my_user_id # if you want to sign the apk
export KEYSTORE_PASS=my_password # ditto
export KEYSTORE_FILE=/path/to/your/keystore
export APPNAME=MyApp
export PACKAGE_NAME=org/ucam/ssb22/html # PLEASE CHANGE THIS

set -e

export PLATFORM=$(find "$ANDROID_HOME"/platforms -maxdepth 1|grep platforms/android-|sort -n|tail -1)
export BUILD_TOOLS=$(find "$ANDROID_HOME"/build-tools -maxdepth 1|sort -n|tail -1)

java_version=$(javac --version|head -1|sed -e 's/javac //' -e 's/[.].*//')
if [ java_version -gt 17 ]; then
    JAVAC=/usr/lib/jvm/java-11-openjdk-amd64/bin/javac
    if ! [ -e $JAVAC ]; then
        echo "javac seems too new for Android's d8, try apt install openjdk-11-jdk (set JAVA_HOME or use update-java-alternatives if necessary)" # this can happen on Ubuntu 24.04 which has 21 (22.04 has 11)
        exit 1
    fi
elif [ java_version -gt 11 ]; then
    JAVAC="javac -source 1.8 -target 1.8" # Debian 12 "Bookworm"
else JAVAC=javac; fi

if [ "$PACKAGE_NAME" == "$(echo -n org/ucam/ssb22/;echo html)" ]; then  # (split so you can still use sed -e on the script)
   echo Please change PACKAGE_NAME before using this script
   exit 1
fi

cd "$APP_WORKSPACE"

sed -e 's/tagetSdkVersion="[0-9]*"/targetSdkVersion="35"/' < AndroidManifest.xml > n && mv n AndroidManifest.xml

rm -rf bin gen && mkdir bin gen
"$BUILD_TOOLS"/aapt package -v -f -I "$PLATFORM"/android.jar -M AndroidManifest.xml -A assets -S res -m -J gen -F bin/resources.ap_
$JAVAC -classpath "$PLATFORM"/android.jar -sourcepath "src;gen" -d "bin" src/$PACKAGE_NAME/*.java gen/$PACKAGE_NAME/R.java
if "$BUILD_TOOLS"/dx --help 2>&1 >/dev/null | grep min-sdk-version >/dev/null; then
    "$BUILD_TOOLS"/dx --min-sdk-version=1 --dex --output=bin/classes.dex bin/ 
elif [ -e "$BUILD_TOOLS"/dx ]; then "$BUILD_TOOLS"/dx --dex --output=bin/classes.dex bin/
else "$BUILD_TOOLS"/d8 --lib "$PLATFORM"/android.jar --min-api 1 --output bin $(find bin -type f -name '*.class'); fi
cp bin/resources.ap_ bin/$APPNAME.ap_ && # change $APPNAME here and all instances below
cd bin
"$BUILD_TOOLS"/aapt add $APPNAME.ap_ classes.dex
cd ..
rm -f bin/$APPNAME.apk ../$APPNAME.apk
if test -e "$BUILD_TOOLS"/apksigner; then
    "$BUILD_TOOLS"/zipalign 4 bin/$APPNAME.ap_ bin/$APPNAME.apk
    "$BUILD_TOOLS"/apksigner sign --ks "$KEYSTORE_FILE" --v1-signer-name "$KEYSTORE_USER" --ks-pass env:KEYSTORE_PASS --key-pass env:KEYSTORE_PASS --out ../$APPNAME.apk bin/$APPNAME.apk
else # old ADT
    jarsigner -sigalg SHA1withRSA -digestalg SHA1 -keystore "$KEYSTORE_FILE" -storepass "$KEYSTORE_PASS" -keypass "$KEYSTORE_PASS" -signedjar bin/$APPNAME.apk bin/$APPNAME.ap_ $KEYSTORE_USER -tsa http://timestamp.digicert.com && # -tsa option requires an Internet connection
        "$BUILD_TOOLS"/zipalign 4 bin/$APPNAME.apk ../$APPNAME.apk
fi
rm bin/*ap_ bin/*apk
cd ..

# Install on any attached devices:
(sleep 300 ; killall adb) & # in case the following command gets stuck when unattended
export adb="$ANDROID_HOME"/platform-tools/adb
for D in $($adb devices|grep device$|cut -f1); do $adb -s "$D" install -r $APPNAME.apk; done || true # no error if no device connected

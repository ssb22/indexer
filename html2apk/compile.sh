#!/bin/bash

export SDK=/usr/local/adt-bundle-mac-x86_64-20140702/sdk # or whatever
export PLATFORM=$SDK/platforms/android-19 # or whatever
export BUILD_TOOLS=$SDK/build-tools/21.0.2 # or whatever
export KEYSTORE_USER=my_user_id # if you want to sign the apk
export KEYSTORE_PASS=my_password # ditto
export APPNAME=MyApp
export PACKAGE_NAME=org/ucam/ssb22/html # PLEASE CHANGE THIS

cd /path/to/your/app/workspace &&

rm -rf bin gen && mkdir bin gen &&
$BUILD_TOOLS/aapt package -v -f -I $PLATFORM/android.jar -M AndroidManifest.xml -A assets -S res -m -J gen -F bin/resources.ap_ &&
javac -classpath $PLATFORM/android.jar -sourcepath "src;gen" -d "bin" src/$PACKAGE_NAME/*.java gen/$PACKAGE_NAME/R.java &&
$BUILD_TOOLS/dx --dex --output=bin/classes.dex bin/ &&
cp bin/resources.ap_ bin/$APPNAME.ap_ && # change $APPNAME here and all instances below
cd bin &&
$BUILD_TOOLS/aapt add $APPNAME.ap_ classes.dex &&
cd .. &&
jarsigner -sigalg SHA1withRSA -digestalg SHA1 -keystore ../keystore -storepass $KEYSTORE_PASS -keypass $KEYSTORE_PASS -signedjar bin/$APPNAME.apk bin/$APPNAME.ap_ $KEYSTORE_USER -tsa http://timestamp.digicert.com && # -tsa option requires an Internet connection
rm -f ../$APPNAME.apk &&
$BUILD_TOOLS/zipalign 4 bin/$APPNAME.apk ../$APPNAME.apk &&
rm bin/*ap_ bin/*apk &&
cd .. || exit 1
adb -d install -r $APPNAME.apk || true # no error if device not connected
